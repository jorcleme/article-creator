import json
import requests
import re
import uuid
from bs4 import BeautifulSoup, Tag
from typing import List, Iterator, Dict, Any
from langchain_text_splitters import TextSplitter
from langchain.schema import Document
from langchain_core.document_loaders import BaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


class SupportingDocumentsLoader(BaseLoader):
    """
    A class for loading Cisco supporting documents.

    At the moment, it supports loading of Admin Guide and CLI Guide documents.

    The main class entry method is `from_url`, which expects a url like this:

    https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html

    It then parses the Book Table of Contents structure to get the paths to the individual documents.

    The `load` method fetches the documents from the paths and returns a list of Document objects.

    Example:
        ```python
        loader = SupportingDocumentsLoader.from_url("https://www.cisco.com/c/en/us/td/docs/switches/lan/csbms/CBS_250_350/CLI/cbs-350-cli-.html")
        documents = loader.load()
        ```

    You could also pass a list of URLs to the constructor but it does expect a certain format.
    """

    def __init__(self, paths: List[str]) -> None:
        self.paths = paths
        self.documents: List[Document] = []

    def save_to_json(self, path: str) -> None:
        with open(path, "w") as json_file:
            json_docs = [doc.dict() for doc in self.documents]
            json.dump(json_docs, json_file, indent=4)

    def load(self) -> List[Document]:
        return list(self.lazy_load())

    def load_ag(self) -> List[Document]:
        from pathlib import Path

        try:
            path = Path.joinpath(Path.cwd(), "data", "etc", "admin_guide_docs.json")
            with path.open("r") as json_file:
                data = json.load(json_file)
                self.documents = [
                    Document(page_content=doc["page_content"], metadata=doc["metadata"])
                    for doc in data
                ]
                return self.documents
        except Exception as e:
            self.documents = list(self.lazy_load())
            self.save_to_json("./data/admin_guide_docs.json")
            return self.documents

    def load_cli(self) -> List[Document]:
        from pathlib import Path

        try:
            path = Path.joinpath(Path.cwd(), "data", "etc", "cli_guide_docs.json")
            with path.open("r") as json_file:
                data = json.load(json_file)
                self.documents = [
                    Document(page_content=doc["page_content"], metadata=doc["metadata"])
                    for doc in data
                ]
                return self.documents
        except Exception as e:
            self.documents = list(self.lazy_load())
            self.save_to_json("./data/cli_guide_docs.json")
            return self.documents

    def lazy_load(self) -> Iterator[Document]:
        for path in self.paths:
            yield from self._fetch(path)

    def _fetch(self, path: str):
        response = requests.get(path)
        response.raise_for_status()
        page_content = response.text
        soup = BeautifulSoup(page_content, "html.parser")
        chapter_content = soup.find("div", id="chapterContent")
        topic_data = self._parse_content(chapter_content)
        metadatas = [
            self._build_metadata(soup, path, topic=data["topic"]) for data in topic_data
        ]
        for data, meta in zip(topic_data, metadatas):
            if data["text"] == "This chapter contains the following sections:":
                continue
            yield Document(page_content=data["text"], metadata=meta)

    def load_schema(self):
        return list(self.lazy_load_cli_schema())

    def lazy_load_cli_schema(self):
        for path in self.paths:
            yield from self._fetch_cli(path)

    def _fetch_cli(self, path: str):
        response = requests.get(path)
        response.raise_for_status()
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        topic_data = self._parse_cli_guide(soup)
        metadatas = [self._build_metadata(soup, path) for data in topic_data]
        for data, meta in zip(topic_data, metadatas):
            if not data.get("syntax") and not data.get("description"):
                continue
            yield {**data, **meta}

    @classmethod
    def from_url(cls, url: str) -> "SupportingDocumentsLoader":
        """
        Create a SupportingDocumentsLoader instance from a given URL.

        Args:
            url (str): The URL to fetch the supporting documents from.

        Returns:
            SupportingDocumentsLoader: An instance of the SupportingDocumentsLoader class.

        Raises:
            requests.HTTPError: If there is an HTTP error while fetching the URL.
        """
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        toc = soup.select("ul#bookToc > li > a")
        links = [f"https://www.cisco.com{link.get('href')}" for link in toc]
        return cls(paths=links)

    @staticmethod
    def sanitize_text(text: str) -> str:
        cleaned_text = re.sub(r"\s+", " ", text.strip())
        cleaned_text = cleaned_text.replace("\\", "")
        cleaned_text = cleaned_text.replace("#", " ")
        cleaned_text = re.sub(r"([^\w\s])\1*", r"\1", cleaned_text)
        return cleaned_text

    @staticmethod
    def _build_metadata(soup: BeautifulSoup, url: str, **kwargs) -> Dict[str, str]:
        """Build metadata from BeautifulSoup output.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object containing the parsed HTML.
            url (str): The URL of the source.
            **kwargs: Additional keyword arguments.

        Returns:
            Dict[str, str]: The metadata dictionary containing the extracted information.
        """
        metadata = {"source": url}
        if title := soup.find("meta", attrs={"name": "description"}):
            metadata["title"] = title.get("content", "Chapter not found.")
        if html := soup.find("html"):
            metadata["language"] = html.get("lang", "No language found.")
        if concept := soup.find("meta", attrs={"name": "concept"}):
            metadata["concept"] = concept.get("content", "No concept found.")
        if topic := kwargs.get("topic"):
            metadata["topic"] = topic
        metadata["doc_id"] = str(uuid.uuid4())
        return metadata

    def _parse_content(self, content: Tag) -> List[Dict[str, Any]]:
        """This method is useful for parsing the content of the Admin Guide or CLI Guide into a large chunk of text and topics suitable for LCEL Documents"""
        articles: List[Tag] = content.find_all("article", class_=("topic", "task"))

        return [
            {
                "topic": self.sanitize_text(
                    article.find(["h2", "h3", "h4"], class_="title").get_text(
                        strip=True
                    )
                ),
                "text": self.sanitize_text(article.get_text()),
            }
            for article in articles
        ]

    def load_and_split(
        self, text_splitter: TextSplitter | None = None
    ) -> List[Document]:
        docs = self.load()
        if text_splitter is None:
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=400, chunk_overlap=50, add_start_index=True
            )
        return text_splitter.split_documents(docs)

    def load_and_split_cli(self, text_splitter: TextSplitter) -> List[Document]:
        docs = self.load_cli()
        return text_splitter.split_documents(docs)

    def load_and_split_ag(self, text_splitter: TextSplitter) -> List[Document]:
        docs = self.load_ag()
        return text_splitter.split_documents(docs)

    def _parse_cli_guide(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parses the CLI Guide only into a suitable schema suitable for Database storage."""

        topic_sections = soup.find_all("section", class_=("body"))

        topic: str = soup.find("meta", attrs={"name": "description"}).get(
            "content", None
        )
        cli_section = []
        for section in topic_sections:
            if re.match(
                r"^This chapter contains the following sections:", section.get_text()
            ):
                continue

            command_name = section.find_previous(class_=("title",)).get_text(strip=True)

            if topic == "Introduction":
                sections = []
                content = {"description": [], "command_name": command_name}
                for child in section.children:
                    if not isinstance(child, Tag):
                        continue
                    if child.name == "p":
                        sections.append(child.get_text())
                    elif child.name == "ul":
                        sub = [li.get_text() for li in child.find_all("li")]
                        sections.extend(sub)
                    elif child.name == "pre":
                        lines = child.get_text().split("\n")
                        sections.extend(lines)
                    else:
                        sections.append(child.get_text())
                content["description"] = list(map(self.sanitize_text, sections))
                content["description"] = list(
                    filter(lambda x: re.match(r"\S", x), content["description"])
                )
                content["topic"] = topic
                print(content)
                cli_section.append(content)
            else:
                sub_sections = section.find_all("section")
                (
                    description,
                    syntax,
                    parameters,
                    default_config,
                    command_mode,
                    user_guidelines,
                    examples,
                ) = (None, None, [], None, None, None, None)
                seen_parameters = set()
                for i, sub in enumerate(sub_sections):
                    if i == 0:
                        description = sub.get_text()
                    elif sub.find(string=re.compile(r"^Syntax", flags=re.I)):
                        paragraphs = sub.find_all("p")
                        syntax = [p.get_text() for p in paragraphs]
                    elif sub.find(string=re.compile(r"^Parameters", flags=re.I)):
                        p = sub.find("p")
                        if p:
                            normalized_text = p.get_text().strip()
                            if normalized_text not in seen_parameters:
                                seen_parameters.add(normalized_text)
                                parameters = [normalized_text]
                        ul = sub.find("ul")
                        if ul:
                            li = ul.find_all("li")
                            for l in li:
                                normalized_text = l.get_text().strip()
                                if normalized_text not in seen_parameters:
                                    seen_parameters.add(normalized_text)
                                    parameters.append(normalized_text)

                    elif sub.find(string=re.compile(r"^Default Configuration")):
                        p = sub.find("p")
                        default_config = p.get_text() if p else sub.get_text()
                    elif sub.find(string=re.compile(r"^Command Mode")):
                        command_mode_p = sub.find("p")
                        command_mode = (
                            command_mode_p.get_text()
                            if command_mode_p
                            else sub.get_text()
                        )
                    elif sub.find(string=re.compile(r"^User Guidelines")):
                        p = sub.find_all("p")
                        if p:
                            user_guidelines = [para.get_text() for para in p]
                            user_guidelines = " ".join(user_guidelines)
                        else:
                            user_guidelines = sub.get_text()
                    elif sub.find(string=re.compile(r"^Examples?")):
                        examples = self._get_examples(sub)
                        print(f"Examples: {examples}")

                cli_section.append(
                    {
                        "topic": topic,
                        "command_name": command_name,
                        "description": (
                            self.sanitize_text(description) if description else None
                        ),
                        "syntax": (
                            list(map(self.sanitize_text, syntax)) if syntax else None
                        ),
                        "parameters": list(map(self.sanitize_text, parameters)),
                        "default_configuration": (
                            self.sanitize_text(default_config)
                            if default_config
                            else None
                        ),
                        "command_mode": (
                            self.sanitize_text(command_mode) if command_mode else None
                        ),
                        "user_guidelines": (
                            self.sanitize_text(user_guidelines)
                            if user_guidelines
                            else None
                        ),
                        "examples": examples,
                    }
                )
        return cli_section

    def _get_examples(self, section: Tag) -> List[Dict[str, Any]]:
        """
        Gets the examples of each section from the CLI Guide.

        Args:
            section (Tag): The section tag containing the examples.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing the examples.
        """
        examples = []
        dic = {}
        desc = section.find("p")
        if desc:
            dic["description"] = self.sanitize_text(desc.get_text())
        ul = section.find("ul")
        if ul:
            li = ul.find_all("li")
            dic["commands"] = [l.get_text() for l in li]
        pre = section.find("pre")
        if pre:
            lines = pre.get_text().split("\n")
            if "commands" in dic:
                dic["commands"].extend(lines)
            else:
                dic["commands"] = lines
        if "commands" in dic:
            dic["commands"] = list(filter(lambda x: x != "", dic["commands"]))
        examples.append(dic)
        return examples


cat_1300_ag_loader = SupportingDocumentsLoader.from_url(
    "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/Admin-Guide/catalyst-1300-admin-guide.html"
)
cat_1300_docs = cat_1300_ag_loader.load()
with open("./data/schema/catalyst_1300_admin_guide.json", "w") as json_file:
    json.dump([doc.dict() for doc in cat_1300_docs], json_file, indent=4)

cat_1300_cli_loader = SupportingDocumentsLoader.from_url(
    "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/cli/C1300-cli.html"
)
cat_1300_cli_docs = cat_1300_cli_loader.load_schema()
with open("./data/schema/catalyst_1300_cli_guide.json", "w") as json_file:
    json.dump(cat_1300_cli_docs, json_file, indent=4)
# cat_1200_ag_loader = SupportingDocumentsLoader.from_url(
#     "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/Admin-Guide/catalyst-1200-admin-guide.html"
# )
# cat_1200_ag_docs = cat_1200_ag_loader.load()
# with open("./data/schema/catalyst_1200_admin_guide.json", "w") as json_file:
#     json.dump([doc.dict() for doc in cat_1200_ag_docs], json_file, indent=4)

# cat_1200_cli_loader = SupportingDocumentsLoader.from_url(
#     "https://www.cisco.com/c/en/us/td/docs/switches/campus-lan-switches-access/Catalyst-1200-and-1300-Switches/cli/C1200-cli.html"
# )
# cat_1200_cli_docs = cat_1200_cli_loader.load_schema()
# with open("./data/schema/catalyst_1200_cli_guide.json", "w") as json_file:
#     json.dump(cat_1200_cli_docs, json_file, indent=4)
