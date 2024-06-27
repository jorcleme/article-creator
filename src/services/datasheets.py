"""
Scrapes Cisco's Support Page Datasheets for product information.
"""

import json
import os
import re
import math
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import pprint

cwd = os.getcwd()

CISCO_CATALYST_1200_SERIES = [
    "C1200-8T-D",
    "C1200-8T-E-2G",
    "C1200-8P-E-2G",
    "C1200-8FP-2G",
    "C1200-16T-2G",
    "C1200-16P-2G",
    "C1200-24T-4G",
    "C1200-24P-4G",
    "C1200-24FP-4G",
    "C1200-48T-4G",
    "C1200-48P-4G",
    "C1200-24T-4X",
    "C1200-24P-4X",
    "C1200-24FP-4X",
    "C1200-48T-4X",
    "C1200-48P-4X",
]

CISCO_CATALYST_1300_SERIES = [
    "C1300-8FP-2G",
    "C1300-8T-E-2G",
    "C1300-8P-E-2G",
    "C1300-16T-2G",
    "C1300-16P-2G",
    "C1300-16FP-2G",
    "C1300-24T-4G",
    "C1300-24P-4G",
    "C1300-24FP-4G",
    "C1300-48T-4G",
    "C1300-48P-4G",
    "C1300-48FP-4G",
    "C1300-16P-4X",
    "C1300-24T-4X",
    "C1300-24P-4X",
    "C1300-24FP-4X",
    "C1300-48T-4X",
    "C1300-48P-4X",
]

CBS_110_BUSINESS_SERIES_UNMANAGED = [
    "CBS110-5T-D",
    "CBS110-8T-D",
    "CBS110-8PP-D",
    "CBS110-16T",
    "CBS110-16PP",
    "CBS110-24T",
    "CBS110-24PP",
]

CBS_220_BUSINESS_SERIES = [
    "CBS220-8T-E-2G",
    "CBS220-8P-E-2G",
    "CBS220-8FP-E-2G",
    "CBS220-16T-2G",
    "CBS220-16P-2G",
    "CBS220-24T-4G",
    "CBS220-24P-4G",
    "CBS220-24FP-4G",
    "CBS220-48T-4G",
    "CBS220-48P-4G",
    "CBS220-24T-4X",
    "CBS220-24P-4X",
    "CBS220-24FP-4X",
    "CBS220-48T-4X",
    "CBS220-48P-4X",
    "CBS220-48FP-4X",
]

CBS_250_BUSINESS_SERIES = [
    "CBS250-8T-D",
    "CBS250-8PP-D",
    "CBS250-8T-E-2G",
    "CBS250-8PP-E-2G",
    "CBS250-8P-E-2G",
    "CBS250-8FP-E-2G",
    "CBS250-16T-2G",
    "CBS250-16P-2G",
    "CBS250-24T-4G",
    "CBS250-24PP-4G",
    "CBS250-24P-4G",
    "CBS250-24FP-4G",
    "CBS250-48T-4G",
    "CBS250-48PP-4G",
    "CBS250-48P-4G",
    "CBS250-24T-4X",
    "CBS250-24P-4X",
    "CBS250-24FP-4X",
    "CBS250-48T-4X",
    "CBS250-48P-4X",
]

CBS_350_BUSINESS_SERIES = [
    "CBS350-8T-E-2G",
    "CBS350-8P-2G",
    "CBS350-8P-E-2G",
    "CBS350-8FP-2G",
    "CBS350-8FP-E-2G",
    "CBS350-8S-E-2G",
    "CBS350-16T-2G",
    "CBS350-16T-E-2G",
    "CBS350-16P-2G",
    "CBS350-16P-E-2G",
    "CBS350-16FP-2G",
    "CBS350-24T-4G",
    "CBS350-24P-4G",
    "CBS350-24FP-4G",
    "CBS350-24S-4G",
    "CBS350-48T-4G",
    "CBS350-48P-4G",
    "CBS350-48FP-4G",
    "CBS350-24T-4X",
    "CBS350-24P-4X",
    "CBS350-24FP-4X",
    "CBS350-48T-4X",
    "CBS350-48P-4X",
    "CBS350-48FP-4X",
    "CBS350-8MGP-2X",
    "CBS350-8MP-2X",
    "CBS350-24MGP-4X",
    "CBS350-12NP-4X",
    "CBS350-24NGP-4X",
    "CBS350-48NGP-4X",
    "CBS350-8XT",
    "CBS350-12XS",
    "CBS350-12XT",
    "CBS350-16XTS",
    "CBS350-24XS",
    "CBS350-24XT",
    "CBS350-24XTS",
    "CBS350-48XT-4X",
]


CBW_100_SERIES_140AC = ["CBW140AC-x"]

CBW_100_SERIES_145AC = ["CBW145AC-x"]

CISCO_110_SERIES_UNMANAGED = [
    "SF110D-05",
    "SF110D-08",
    "SF110D-08HP",
    "SF110D-16",
    "SF110D-16HP",
    "SF110-16",
    "SF110-24",
    "SF112-24",
    "SG110D-05",
    "SG110D-08",
    "SG110D-08HP",
    "SG110-16",
    "SG110-16HP",
    "SG112-24",
    "SG110-24",
    "SG110-24HP",
]

CISCO_350_SERIES_MANAGED_SWITCHES = [
    "SF350-08",
    "SF352-08",
    "SF352-08P",
    "SF352-08MP",
    "SF350-24",
    "SF350-24P",
    "SF350-24MP",
    "SF350-48",
    "SF350-48P",
    "SF350-48MP",
    "SG350-8PD",
    "SG350-10",
    "SG350-10P",
    "SG350-10MP",
    "SG355-10MP",
    "SG350-10SFP",
    "SG350-20",
    "SG350-28",
    "SG350-28P",
    "SG350-28MP",
    "SG350-28SFP",
    "SG350-52",
    "SG350-52P",
    "SG350-52MP",
]

CISCO_350X_STACKABLE_SERIES = [
    "SG350X-8PMD",
    "SG350X-12PMV",
    "SG350X-24P",
    "SG350X-24MP",
    "SG350X-24PD",
    "SG350X-24PV",
    "SG350X-48",
    "SG350X-48P",
    "SG350X-48MP",
    "SG350X-48PV",
    "SG350X-48P",
    "SG350XG-2F10",
    "SG350XG-24F",
    "SG350XG-24T",
    "SG350XG-48T",
    "SX350X-08",
    "SX350X-12",
    "SX350X-24F",
    "SX350X-24",
    "SX350X-52",
]

CISCO_550X_STACKABLE_SERIES = [
    "SF500-24",
    "SF500-24P",
    "SF500-24MP",
    "SF500-48",
    "SF500-48P",
    "SF500-48MP",
    "SG500-28",
    "SG500-28P",
    "SG500-28MPP",
    "SG500-52",
    "SG500-52P",
    "SG500-52MP",
    "SG500X-24",
    "SG500X-24P",
    "SG500X-24MPP",
    "SG500X-48",
    "SG500X-48P",
    "SG500X-48MP",
    "SG500XG-8F8T",
]


CATALYST_1000_SERIES = [
    "C1000-8T-2G-L",
    "C1000-8T-E-2G-L",
    "C1000-8P-2G-L",
    "C1000-8P-E-2G-L",
    "C1000-8FP-2G-L",
    "C1000-8FP-E-2G-L",
    "C1000-16T-2G-L",
    "C1000-16T-E-2G-L",
    "C1000-16P-2G-L",
    "C1000-16P-E-2G-L",
    "C1000-16FP-2G-L",
    "C1000-24T-4G-L",
    "C1000-24P-4G-L",
    "C1000-24FP-4G-L",
    "C1000-48T-4G-L",
    "C1000-48P-4G-L",
    "C1000-48FP-4G-L",
    "C1000-24T-4X-L",
    "C1000-24P-4X-L",
    "C1000-24FP-4X-L",
    "C1000-48T-4X-L",
    "C1000-48P-4X-L",
    "C1000-48FP-4X-L",
    "C1000FE-24T-4G-L",
    "C1000FE-24P-4G-L",
    "C1000FE-48T-4G-L",
    "C1000FE-48P-4G-L",
]


def main(urls: list[dict[str, str]]):
    json_list = []
    for url in urls:
        # initialize a dict to store the data. The dict should be empty at the start of each iteration
        smb_builder = {}
        # make a request to the url
        request = make_request(url=url["url"])
        # parse the request content with BeautifulSoup
        soup = BeautifulSoup(request.content, "html.parser")
        concept = url["concept"]
        if re.search(r"Cisco Catalyst 1000 Series Switches", string=concept):
            sloppy_series_datasheet = process_catalyst_1000_series(soup, smb_builder)
            series_datasheet = transform_catalyst_1000_data(sloppy_series_datasheet)
        elif re.search(r"Cisco 110 Series Unmanaged Switches", string=concept):
            series_datasheet = process_110_series_unmanaged_switch_data(
                soup, smb_builder
            )
        elif re.search(r"Cisco 350 Series Managed Switches", string=concept):
            series_datasheet = process_300_series_managed_switch_data(soup, smb_builder)

        elif re.search(r"Cisco Business Wireless AC", string=concept):
            sub_concept_meta = soup.find("meta", attrs={"name": "title"}).get("content")
            if sub_concept_meta == "Cisco Business 140AC Access Point Data Sheet":
                sub_concept = "CBW140AC"
                series_datasheet[sub_concept] = parse_table(soup=soup, obj=smb_builder)
            elif sub_concept_meta == "Cisco Business 145AC Access Point Data Sheet":
                sub_concept = "CBW145AC"
                series_datasheet[sub_concept] = parse_table(soup=soup, obj=smb_builder)
            elif sub_concept_meta == "Cisco Business 240AC Access Point Data Sheet":
                sub_concept = "CBW240AC"
                series_datasheet[sub_concept] = parse_table(soup=soup, obj=smb_builder)
        elif re.search(r"Cisco Business Wireless AX", string=concept):
            sub_concept_meta = (
                soup.find("meta", attrs={"name": "title"}).get("content").strip()
            )
            if sub_concept_meta == "Cisco Business 150AX Access Point Data Sheet":
                sub_concept = "CBW150AXM"
                series_datasheet[sub_concept] = parse_table(soup=soup, obj=smb_builder)
            elif (
                sub_concept_meta
                == "Cisco Business Wireless 151AXM Mesh Extender Datasheet"
            ):
                sub_concept = "CBW151AXM"
                series_datasheet[sub_concept] = parse_table(soup=soup, obj=smb_builder)
        else:
            series_datasheet = parse_table(soup=soup, obj=smb_builder)
        # final_dict = {}
        # final_dict[concept] = {k: v for k, v in series_datasheet.items()}
        # json_list.append(final_dict)
        # series_datasheet = {}
        output = {"family": concept, "features": series_datasheet}
        json_list.append(output)
        series_datasheet = {}

    with open(
        f"{cwd}/python/data/test_all_datasheets.json", "w+", encoding="utf8"
    ) as file:
        file.write(json.dumps(json_list, indent=4, ensure_ascii=True))


def process_110_series_unmanaged_switch_data(
    soup: BeautifulSoup, smb_builder: dict
) -> dict:
    rows = soup.select("tbody > tr")
    desired_headers = [
        "physical_dimensions",
        "weight",
        "ports",
        "switching_capacity",
        "forwarding_capacity",
    ]
    for row in rows:
        cells = [
            cell.get_text(strip=True, separator=" ")
            for cell in row.find_all("td")
            if re.search(r".+", string=cell.get_text(strip=True, separator=" "))
        ]
        print(f"cells: {cells}")
        determine_key = row.select("td")[0].text.strip()
        print(f"determine_key: {determine_key}")
        if determine_key in CISCO_110_SERIES_UNMANAGED:
            key = determine_key
        else:
            key = create_joined_header(determine_key.lower()).strip()
        try:
            values = [
                strng.get_text(strip=True, separator=" ")
                for strng in row.select("td")[1].contents[1::2]
            ]

            if key in desired_headers:
                for value in values:
                    model, data_entry = value.split(":")
                    if model.strip() in CISCO_110_SERIES_UNMANAGED:
                        if model not in smb_builder:
                            smb_builder[model] = {}
                        smb_builder[model][key] = data_entry.strip()

            elif key == "power_over_ethernet":
                model_names = [
                    strng.get_text(strip=True, separator=" ")
                    for strng in row.select("td")[1].find_all("p")
                    if not re.search(r"Model Name", strng.get_text(strip=True))
                ]
                power_dedicated_to_poe = [
                    strng.get_text(strip=True, separator=" ")
                    for strng in row.select("td")[2].find_all("p")
                    if not re.search(
                        r"Power Dedicated to PoE", strng.get_text(strip=True)
                    )
                ]
                number_of_ports_that_support_poe = [
                    strng.get_text(strip=True, separator=" ")
                    for strng in row.select("td")[3].find_all("p")
                    if not re.search(r"Number of PoE Ports", strng.get_text(strip=True))
                ]
                for i, model in enumerate(model_names):
                    if model not in smb_builder:
                        smb_builder[model] = {}
                    smb_builder[model]["power_dedicated_to_poe"] = (
                        power_dedicated_to_poe[i]
                    )
                    smb_builder[model]["number_of_ports_that_support_poe"] = (
                        number_of_ports_that_support_poe[i]
                    )
                print(f"model_names: {model_names}")

            elif key and len(values) == 1:
                smb_builder[key] = values.pop(0)
            else:
                data = []
                for data_entry in values:
                    data.append(data_entry)
                smb_builder[key] = data
        except (IndexError, ValueError) as e:
            print(f"Caught an exception of type {type(e).__name__}: {e}")
            continue
    return smb_builder


def process_300_series_managed_switch_data(
    soup: BeautifulSoup, smb_builder: dict
) -> dict:
    headers_needing_iteration = ["Model", "Model Name"]
    rows = soup.select("tbody > tr")
    skip_count = 0
    for row in rows:
        if skip_count > 0:
            skip_count -= 1
            continue
        cells = [
            cell.get_text(strip=True, separator=" ")
            for cell in row.find_all("td")
            if re.search(r".+", string=cell.get_text(strip=True, separator=" "))
        ]
        print(f"cells: {cells}")
        if len(cells) == 1:
            continue
        if len(cells) == 2:
            key = create_joined_header(cells[0])
            value = cells[1]
            if not key.startswith("-") and value:
                smb_builder[key] = value
        if any(header in cells for header in headers_needing_iteration):
            if "Power Dedicated to PoE" in cells:
                rowspan = 14
                smb_builder = parse_row_data(
                    rowspan=rowspan,
                    cells=cells,
                    row=row,
                    obj=smb_builder,
                    length=len(cells),
                )
                skip_count = rowspan
            else:
                smb_builder = parse_row_data(
                    rowspan=len(CISCO_350_SERIES_MANAGED_SWITCHES),
                    cells=cells,
                    row=row,
                    obj=smb_builder,
                    length=len(cells),
                )
                skip_count = len(CISCO_350_SERIES_MANAGED_SWITCHES)
    return smb_builder


def normalize_other_series_data(json: dict) -> dict:
    """_summary_

    Args:
        json (dict): The input JSON data to be transformed.

    Returns:
        dict: The transformed JSON data.
    """
    devices = {k: v for k, v in json.items() if k in COMBINED_SERIES}

    for device, attributes in devices.items():
        # 110 Series Unmanaged Switches have no fans except for SG100-24HP
        if device in CISCO_110_SERIES_UNMANAGED:
            if device == "SG100-24HP":
                attributes["fan"] = "Yes"
            else:
                attributes["fan"] = "No"
        if "forwarding_capacity" in attributes:
            attributes["forwarding_rate"] = attributes["forwarding_capacity"]
            del attributes["forwarding_capacity"]

        if "rj-45_ports" in attributes:
            match = re.match(r"(\d+)", attributes["rj-45_ports"])
            if match:
                num_ports = match.group(1)
                attributes["rj-45_ports"] = f"{num_ports} x Gigabit Ethernet"
                if num_ports == "8":
                    attributes["forwarding_rate"] = 14.88
                    attributes["switching_capacity"] = 20.0
                    attributes["mtbf"] = int(2171669)
                elif num_ports == "16":
                    attributes["mtbf"] = int(2165105)
                    attributes["forwarding_rate"] = 26.78
                    attributes["switching_capacity"] = 36.0
                elif num_ports == "24":
                    attributes["mtbf"] = int(2026793)
                    if "FE" in device:
                        attributes["forwarding_rate"] = 9.52
                        attributes["switching_capacity"] = 12.8
                    elif "uplink_ports" in attributes and re.search(
                        r"\bSFP\b(?!\+)", attributes["uplink_ports"]
                    ):
                        attributes["forwarding_rate"] = 41.67
                        attributes["switching_capacity"] = 56.0
                    else:
                        attributes["forwarding_rate"] = 95.23
                        attributes["switching_capacity"] = 128.0
                elif num_ports == "48":
                    attributes["mtbf"] = int(1452667)
                    if "FE" in device:
                        attributes["forwarding_rate"] = 13.09
                        attributes["switching_capacity"] = 17.6
                    elif "uplink_ports" in attributes and re.search(
                        r"\bSFP\b(?!\+)", attributes["uplink_ports"]
                    ):
                        attributes["forwarding_rate"] = 77.38
                        attributes["switching_capacity"] = 104.0
                    else:
                        attributes["forwarding_rate"] = 130.94
                        attributes["switching_capacity"] = 176.0

        if "uplink_ports" in attributes:
            num_ports = re.match(r"(\d+)", attributes["uplink_ports"]).group(1)
            if "SFP+" in attributes["uplink_ports"]:
                attributes["uplink_ports"] = (
                    f"{num_ports} 10G SFP+{' combo' if 'combo' in attributes['uplink_ports'].lower() else ''}"
                )
            elif "SFP" in attributes["uplink_ports"]:
                attributes["uplink_ports"] = (
                    f"{num_ports} Gigabit Ethernet SFP{' combo' if 'combo' in attributes['uplink_ports'].lower() else ''}"
                )

        json[device] = attributes
    return json


def transform_catalyst_1000_data(json):
    """
    Transforms the given data based on the following rules:
    1. For the "fan" property, converts 'Y' to 'No' and otherwise to 'Yes'.
    2. Appends "kg" to "unit_weight".
    3. Updates the "rj-45_ports" to "8 x Gigabit Ethernet".
    4. Transforms the "uplink_ports" based on the provided logic.

    Args:
    - json (dict): The input JSON data to be transformed.

    Returns:
    - dict: The transformed JSON data.
    """

    devices = {k: v for k, v in json.items() if k in CATALYST_1000_SERIES}

    for device, attributes in devices.items():
        if "fan" in attributes:
            attributes["fan"] = "No" if attributes["fan"] == "Y" else "Yes"

        if "unit_weight" in attributes:
            attributes["unit_weight"] += " kg"

        if "rj-45_ports" in attributes:
            match = re.match(r"(\d+)", attributes["rj-45_ports"])
            if match:
                num_ports = match.group(1)
                attributes["rj-45_ports"] = f"{num_ports} x Gigabit Ethernet"
                if num_ports == "8":
                    attributes["forwarding_rate"] = 14.88
                    attributes["switching_capacity"] = 20.0
                    attributes["mtbf"] = int(2171669)
                elif num_ports == "16":
                    attributes["mtbf"] = int(2165105)
                    attributes["forwarding_rate"] = 26.78
                    attributes["switching_capacity"] = 36.0
                elif num_ports == "24":
                    attributes["mtbf"] = int(2026793)
                    if "FE" in device:
                        attributes["forwarding_rate"] = 9.52
                        attributes["switching_capacity"] = 12.8
                    elif "uplink_ports" in attributes and re.search(
                        r"\bSFP\b(?!\+)", attributes["uplink_ports"]
                    ):
                        attributes["forwarding_rate"] = 41.67
                        attributes["switching_capacity"] = 56.0
                    else:
                        attributes["forwarding_rate"] = 95.23
                        attributes["switching_capacity"] = 128.0
                elif num_ports == "48":
                    attributes["mtbf"] = int(1452667)
                    if "FE" in device:
                        attributes["forwarding_rate"] = 13.09
                        attributes["switching_capacity"] = 17.6
                    elif "uplink_ports" in attributes and re.search(
                        r"\bSFP\b(?!\+)", attributes["uplink_ports"]
                    ):
                        attributes["forwarding_rate"] = 77.38
                        attributes["switching_capacity"] = 104.0
                    else:
                        attributes["forwarding_rate"] = 130.94
                        attributes["switching_capacity"] = 176.0

        if "uplink_ports" in attributes:
            num_ports = re.match(r"(\d+)", attributes["uplink_ports"]).group(1)
            if "SFP+" in attributes["uplink_ports"]:
                attributes["uplink_ports"] = (
                    f"{num_ports} 10G SFP+{' combo' if 'combo' in attributes['uplink_ports'].lower() else ''}"
                )
            elif "SFP" in attributes["uplink_ports"]:
                attributes["uplink_ports"] = (
                    f"{num_ports} Gigabit Ethernet SFP{' combo' if 'combo' in attributes['uplink_ports'].lower() else ''}"
                )

        json[device] = attributes
    return json


def process_catalyst_1000_series(soup: BeautifulSoup, smb_builder: dict) -> dict:
    def iterate_cataylst_table_section(index, row, array):
        """Iterates through a table section and appends to an array for Catalyst 1000"""
        i = index
        while i:
            row = row.find_next("tr")
            new_cells = [
                cell.get_text(strip=True, separator=" ") for cell in row.contents[1::2]
            ]
            array.append(new_cells)
            i -= 1

    HEADERS1 = [
        "rj-45_ports",
        "uplink_ports",
        "power_dedicated_to_poe",
        "fan",
        "unit_dimensions",
        "unit_weight",
    ]
    HEADERS2 = [
        "8-port models",
        "16-port models",
        "24-port models (1/10G uplinks)",
        "48-port models (1/10G uplinks)",
    ]

    model_info = []
    port_model_info = []
    generic_series_info = []
    management_info = []

    undesired_headers = ["Product number", "Note:", "Note", "*Note:"]

    for row in soup.find_all("tr"):
        cells = [
            cell.get_text(strip=True, separator=" ") for cell in row.contents[1::2]
        ]
        cells = list(filter(lambda element: re.search(r".+", string=element), cells))
        print(f"cells: {cells}")
        # clean_cells = list(filter(lambda element: re.search(r'.+', string=element), cells))
        if cells and cells[0] in CATALYST_1000_SERIES:
            model_info.append(cells)
        if len(cells) == 1:
            continue
        if len(cells) == 5 and "8-port models" in cells:
            iterate_cataylst_table_section(30, row=row, array=port_model_info)
        if (
            len(cells) == 2
            and not any(word in cells for word in CATALYST_1000_SERIES)
            and not any(word in cells for word in undesired_headers)
        ):
            generic_series_info.append(cells)

        desired_generic_headers = ["Management", "Standards", "RFC compliance"]
        if (len(cells) == 4 or len(cells) == 3) and any(
            word in cells for word in desired_generic_headers
        ):
            cells[0] = create_joined_header(cells[0])
            management_info.append(cells)

    header1_to_model = model_info[: len(CATALYST_1000_SERIES)]

    for array in header1_to_model:
        key = array.pop(0)
        print(f"key: {key}")
        smb_builder[key] = dict(zip(HEADERS1, array))

    for array in port_model_info:
        key = array.pop(0)
        smb_builder[key] = dict(zip(HEADERS2, array))

    for array in generic_series_info:
        key = create_joined_header(array.pop(0))
        smb_builder[key] = array[0]

    for array in management_info:
        key = array.pop(0)
        smb_builder[key] = array

    return smb_builder


def handle_table_data(headers_map: list[str], table_data: list[str], obj: dict) -> dict:
    """
    Processes table data based on header map and updates the given object.

    :param headers_map: List of headers.
    :param table_data: List of table data.
    :param obj: Object to update with the processed data.
    :return: Updated object.
    """
    model = table_data.pop(0)
    if model not in obj:
        obj[model] = {}

    convert_keys = {
        "switching_capacity": lambda x: (
            "switching_capacity",
            float(x.replace(",", "")),
        ),
        "forwarding_rate": lambda x: ("forwarding_rate", float(x.replace(",", ""))),
        "combo_ports": lambda x: ("uplink_ports", x),
        "dimensions": lambda x: ("unit_dimensions", x),
        "poe_power_budget": lambda x: ("power_dedicated_to_poe", x),
        "number_of_ports_that_support_poe": lambda x: (
            "number_of_ports_that_support_poe",
            int(re.search(r"^\d+", x).group(0)) if re.search(r"^\d+", x) else 0,
        ),
        "heat_dissipation": lambda x: ("heat_dissipation", float(x.replace(",", ""))),
        "capacity_in_millions_of_packets_per_second": lambda x: (
            "forwarding_rate",
            float(x.replace(",", "")),
        ),
        "switching_capacity_in_gigabits_per_second": lambda x: (
            "switching_capacity",
            float(x.replace(",", "")),
        ),
        "mtbf": lambda x: ("mtbf", int(x.replace(",", ""))),
    }

    for index, data in enumerate(table_data):
        key = headers_map[index]
        conversion = convert_keys.get(key)
        if conversion:
            try:
                new_key, value = conversion(data)
                obj[model][new_key] = value
            except Exception as e:
                print(f"Error in converting key '{key}' with value '{data}': {e}")
        else:
            obj[model][key] = data

    return obj


def parse_row_data(rowspan: int, cells: list[str], row: Tag, obj: dict, length: int):
    undesired_headers = [
        "Model",
        "Model Name",
        "Model name",
        "SKU",
        "Product Name",
        "Product name",
        "Product Ordering Number",
    ]

    cells = [cell for cell in cells if cell not in undesired_headers]
    if length % 2 == 0:
        headers_slice = (math.floor(length / 2) * -1) - 1
    else:
        headers_slice = math.ceil(length / 2) * -1
    unformatted_headers = cells[headers_slice::]
    headers_map = list(dict.fromkeys(map(create_joined_header, unformatted_headers)))
    print(f"headers_map: {headers_map}")

    for _ in range(rowspan):
        row = row.find_next("tr")
        table_data = [
            cell.get_text(strip=True, separator=" ")
            for cell in row.find_all("td")
            if re.search(r".+", string=cell.get_text(strip=True, separator=" "))
        ]
        print(f"table_data: {table_data}")
        try:
            obj = handle_table_data(headers_map, table_data, obj)
        except Exception as e:
            pass
    return obj


def parse_table(soup: BeautifulSoup, obj: dict):
    desired_titles = [
        "Model",
        "Model Name",
        "Model name",
        "SKU",
        "Product Name",
        "Product name",
        "Product Ordering Number",
        "Data rates supported",
        "General",
    ]
    rows = soup.select("tbody > tr")
    skip_count = 0
    for row in rows:
        if skip_count > 0:
            skip_count -= 1
            continue

        rowspan = int(row.find_next("td").get("rowspan", "0"))
        cell_data_text = [
            cell.get_text(strip=True)
            for cell in row.find_all("td")
            if re.search(r".+", string=cell.get_text(strip=True, separator=" "))
        ]
        print(f"cell data: {cell_data_text}")
        if rowspan > 1 and any(word in cell_data_text for word in desired_titles):
            smb_builder = parse_row_data(
                rowspan=rowspan - 1,
                cells=cell_data_text,
                row=row,
                obj=obj,
                length=len(cell_data_text),
            )
            # update obj with smb_builder data
            obj.update(smb_builder)

            # print(f"obj: {pprint.pformat(obj)}")
            skip_count = rowspan - 1
        elif rowspan > 1 and not any(word in cell_data_text for word in desired_titles):
            # Then we need to get the next row and parse it
            new_row = row.find_next("tr")
            new_unformatted_cells = [
                cell.get_text(strip=True, separator=" ")
                for cell in new_row.find_all("td")
            ]
            smb_builder = parse_row_data(
                rowspan=rowspan - 2,
                cells=new_unformatted_cells,
                row=new_row,
                obj=obj,
                length=len(new_unformatted_cells),
            )
            obj.update(smb_builder)
            skip_count = rowspan - 1
        elif rowspan == 0 and len(cell_data_text) == 2:
            key = create_joined_header(cell_data_text[0])
            if len(row.contents) > 1:
                list_like = row.contents[3]
                value = [
                    strng.get_text(strip=True, separator=" ")
                    for strng in list_like.find_all(["p", "li"])
                ]
                if len(value) == 1:
                    value = value[0]
            else:
                value = cell_data_text[1]
            if not key.startswith("-") and value:
                obj[key] = value
        else:
            continue
    return obj


urls = [
    dict(
        concept="Cisco Business 110 Series Unmanaged Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/business-110-series-unmanaged-switches/datasheet-c78-744158.html?ccid=cc001531",
    ),
    # dict(
    #     concept="Cisco 110 Series Unmanaged Switches",
    #     url="https://www.cisco.com/c/en/us/products/collateral/switches/110-series-unmanaged-switches/datasheet-c78-734450.html",
    # ),
    dict(
        concept="Cisco Business 220 Series Smart Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/business-220-series-smart-switches/datasheet-c78-744915.html",
    ),
    dict(
        concept="Cisco Business 250 Series Smart Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/business-250-series-smart-switches/nb-06-bus250-smart-switch-ds-cte-en.html",
    ),
    dict(
        concept="Cisco Business 350 Series Managed Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/business-350-series-managed-switches/datasheet-c78-744156.html",
    ),
    dict(
        concept="Cisco Catalyst 1000 Series Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1000-series-switches/nb-06-cat1k-ser-switch-ds-cte-en.html",
    ),
    dict(
        concept="Cisco Catalyst 1200 Series Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-ser-data-sheet-cte-en.html",
    ),
    dict(
        concept="Cisco Catalyst 1300 Series Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1300-series-switches/nb-06-cat1300-ser-data-sheet-cte-en.html",
    ),
    dict(
        concept="Cisco 350 Series Managed Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/small-business-smart-switches/data-sheet-c78-737359.html",
    ),
    dict(
        concept="Cisco 350X Series Stackable Managed Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/350x-series-stackable-managed-switches/datasheet-c78-735986.html",
    ),
    dict(
        concept="Cisco 550X Series Stackable Managed Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/550x-series-stackable-managed-switches/datasheet-c78-735874.html",
    ),
    dict(
        concept="Cisco 250 Series Smart Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/250-series-smart-switches/datasheet-c78-737061.html",
    ),
    dict(
        concept="Cisco 220 Series Smart Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/small-business-220-series-smart-plus-switches/datasheet-c78-731284.html",
    ),
    dict(
        concept="Cisco 300 Series Managed Switches",
        url="https://www.cisco.com/c/en/us/products/collateral/switches/small-business-smart-switches/data_sheet_c78-610061.html",
    ),
    dict(
        concept="Cisco Business Wireless AC",
        url="https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-access-points/smb-01-bus-140ac-ap-ds-cte-en.html",
    ),
    dict(
        concept="Cisco Business Wireless AC",
        url="https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-access-points/smb-01-bus-145ac-ap-ds-cte-en.html",
    ),
    dict(
        concept="Cisco Business Wireless AC",
        url="https://www.cisco.com/c/en/us/products/collateral/wireless/business-200-series-access-points/smb-01-bus-240ac-ap-ds-cte-en.html",
    ),
    dict(
        concept="Cisco Business Wireless AX",
        url="https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-access-points/business-access-point-ds.html",
    ),
    dict(
        concept="Cisco Business Wireless AX",
        url="https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-mesh-extenders/busines-mesh-extender-ds.html",
    ),
]
# urls = [
#     "https://www.cisco.com/c/en/us/products/collateral/switches/business-110-series-unmanaged-switches/datasheet-c78-744158.html?ccid=cc001531",
#     "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1200-series-switches/nb-06-cat1200-ser-data-sheet-cte-en.html",
#     "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1300-series-switches/nb-06-cat1300-ser-data-sheet-cte-en.html",
#     "https://www.cisco.com/c/en/us/products/collateral/switches/business-220-series-smart-switches/datasheet-c78-744915.html#Productspecifications",
#     "https://www.cisco.com/c/en/us/products/collateral/switches/business-250-series-smart-switches/nb-06-bus250-smart-switch-ds-cte-en.html",
#     "https://www.cisco.com/c/en/us/products/collateral/switches/business-350-series-managed-switches/datasheet-c78-744156.html",
#     "https://www.cisco.com/c/en/us/products/collateral/switches/catalyst-1000-series-switches/nb-06-cat1k-ser-switch-ds-cte-en.html",
#     "https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-access-points/smb-01-bus-140ac-ap-ds-cte-en.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-access-points/smb-01-bus-145ac-ap-ds-cte-en.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/business-200-series-access-points/smb-01-bus-240ac-ap-ds-cte-en.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-access-points/business-access-point-ds.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/business-100-series-mesh-extenders/busines-mesh-extender-ds.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/routers/small-business-rv-series-routers/datasheet-c78-742350.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/switches/110-series-unmanaged-switches/datasheet-c78-734450.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/switches/small-business-200-series-smart-switches/data_sheet_c78-634369.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/switches/250-series-smart-switches/datasheet-c78-737061.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/switches/small-business-smart-switches/data_sheet_c78-610061.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/switches/350x-series-stackable-managed-switches/datasheet-c78-735986.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/switches/550x-series-stackable-managed-switches/datasheet-c78-735874.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-500-series-wireless-access-points/data_sheet_c78-727995.html",
#     # 'https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-500-series-wireless-access-points/datasheet-c78-738872.html',
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-500-series-wireless-access-points/datasheet-c78-736449.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-300-series-wireless-access-points/datasheet-c78-736452.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/wap321-wireless-n-selectable-band-access-point-single-point-setup/c78-697406_data_sheet.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-300-series-wireless-access-points/datasheet-c78-733625.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-300-series-wireless-access-points/datasheet-c78-732143.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/routers/rv320-dual-gigabit-wan-vpn-router/data_sheet_c78-726132.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/routers/rv260-vpn-router/datasheet-c78-741409.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/routers/rv160-vpn-router/datasheet-c78-741410.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/wap121-wireless-n-access-point-single-point-setup/c78-697404_data_sheet.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-100-series-wireless-access-points/datasheet-c78-738881.html",
#     # "https://www.cisco.com/c/en/us/products/collateral/wireless/small-business-100-series-wireless-access-points/datasheet-c78-736450.html"
# ]


COMBINED_SERIES = (
    CBS_220_BUSINESS_SERIES
    + CBS_250_BUSINESS_SERIES
    + CBS_350_BUSINESS_SERIES
    + CATALYST_1000_SERIES
    + CBW_100_SERIES_140AC
    + CISCO_110_SERIES_UNMANAGED
    + CBW_100_SERIES_145AC
    + CISCO_110_SERIES_UNMANAGED
    + CISCO_CATALYST_1200_SERIES
    + CISCO_CATALYST_1300_SERIES
    + CISCO_350_SERIES_MANAGED_SWITCHES
    + CBS_110_BUSINESS_SERIES_UNMANAGED
)

corrected_dict = {}


def make_request(url):
    """Takes a URL and returns a request object"""
    return requests.get(url=url, timeout=3000)


def create_joined_header(key: str):
    """Takes a string and returns a joined header"""
    refined_key = re.sub(r"\([^)]*\)", repl="", string=key.lower()).replace("/", " ")
    joined_header = (
        "_".join(["".join(y) for y in [x for x in refined_key.split()]])
        .replace(",", "")
        .replace(":", "")
    )
    # if forwaring_rate_millions_of_packets_per_second is in the header, then replace it with forwarding_rate
    if (
        "forwarding_rate" in joined_header
        or "capacity_in_millions_of_packets" in joined_header
        or "capacity_in_mpps" in joined_header
    ):
        joined_header = "forwarding_rate"
    # if switching_capacity" in the joined_header, then replace it with switching_capacity
    if "switching_capacity" in joined_header:
        joined_header = "switching_capacity"
    # if "mtbf" in the joined_header, then replace it with mtbf
    if "mtbf" in joined_header:
        joined_header = "mtbf"
    if "power_consumption:_worst_case" in joined_header:
        joined_header = "power_consumption"
    return joined_header


main(urls=urls)
