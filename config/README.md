# config/manifest file
`cae-np-alln-cxdetesting-dev.yaml` is of the format `cae-np-<location>-<namespace>-<prod/stage/dev>.yaml`

Contents:
- Replace `{{appName}}` with the app name, preferably in the format `cecid-appname`.
- Replace `{{softwareId}}` with the software ID from CoDE. It is just used for labels afaik, so if not feasible, can be skipped.

```yaml
---
# App deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: '{{appName}}'
  namespace: 'cxdetesting'
  labels:
    softwareId: '{{softwareId}}'
    softwareName: '{{appName}}'
spec:
  selector:
    matchLabels:
      app: '{{appName}}'
  replicas: 1
  template:
    metadata:
      namespace: 'cxdetesting'
      labels:
        app: '{{appName}}'
        environment: 'stage'
        softwareId: '{{softwareId}}'
        softwareName: '{{appName}}'
    spec:
      containers:
      - image: 'containers.cisco.com/proseide/{{appName}}:${trigger["parameters"]["imageTag"]}'
        imagePullPolicy: Always
        name: '{{appName}}'
        ports:
        - containerPort: 5000
        env:
        - name: MONGO_URI
          value: 'mongodb://{{appName}}-mongo-service:27017/{{appName}}'
      imagePullSecrets:
      - name: proseide-cdconsole-bot-pull-secret

---
# App service exposing port 5000
apiVersion: v1
kind: Service
metadata:
  name: '{{appName}}-service'
  namespace: 'cxdetesting'
  labels:
    softwareId: '{{softwareId}}'
    softwareName: '{{appName}}'
spec:
  ports:
    - name: "web"
      protocol: "TCP"
      port: 5000
  selector:
      app: '{{appName}}'
  type: ClusterIP

---
# Ingress pointing to app port 5000
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: {{appName}}-deployment
  namespace: cxdetesting
spec:
  host: {{appName}}.cisco.com
  to:
    kind: Service
    name: {{appName}}-service
  tls:
    termination: edge
  port:
    targetPort: web

---
# Mongo deployment, does not persist data on container recreates for now.
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{appName}}-mongo-deployment
  namespace: cxdetesting
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {{appName}}-mongo
  template:
    metadata:
      labels:
        app: {{appName}}-mongo
    spec:
      containers:
        - image: containers.cisco.com/proseide/mongo
          imagePullPolicy: Always
          name: mongo
          ports:
            - containerPort: 27017
          volumeMounts:
            - name: mongodata
              mountPath: /data/db
              subPath: db
            - name: mongodata
              mountPath: /data/configdb
              subPath: configdb
      volumes:
        - name: mongodata
          persistentVolumeClaim: 
            claimName: {{appName}}-pvc

---
# Mongo service on port 27017
apiVersion: v1
kind: Service
metadata:
  name: '{{appName}}-mongo-service'
  namespace: 'cxdetesting'
spec:
  ports:
    - protocol: "TCP"
      port: 27017
  selector:
      app: '{{appName}}-mongo'
  type: ClusterIP

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: {{appName}}-pvc
  namespace: cxdetesting
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  resources:
    requests:
      storage: 1Gi

```

