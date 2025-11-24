# QnA-Agent: Production Readiness TODO

This document outlines the key considerations and action items required to make the QnA-Agent service ready for a production deployment, particularly in a Kubernetes (K8s) environment.

---

### 1. How would you handle sensitive configuration in K8S environments?

**Answer:** The best practice is to use **Kubernetes Secrets**. Sensitive data like API keys should never be stored in configuration files, environment files, or Docker images.

**TODO:**
- [ ] **Create Kubernetes Secret Manifests**: Define a `Secret` manifest (e.g., `k8s/secrets.yaml`) to hold sensitive values like `OPENAI_API_KEY`. This file should be managed securely and excluded from public source control.
- [ ] **Mount Secrets as Environment Variables**: Update the application's `Deployment` manifest (`k8s/deployment.yaml`) to mount the values from the Kubernetes Secret directly into the application container as environment variables.
- [ ] **Update Configuration Loading**: Ensure the application's settings logic (`app/core/config.py`) is configured to read these secrets from the environment, which it already does. This requires no code change, only a configuration change in the deployment environment.

---

### 2. What endpoints would help orchestration systems manage service lifecycle?

**Answer:** Orchestration systems like Kubernetes rely on **health check endpoints** (probes) to manage a container's lifecycle (e.g., to know when to restart it or send traffic to it).

**TODO:**
- [ ] **Implement a Liveness Probe**: Create a `/health/live` endpoint. This endpoint should return a simple `200 OK` response to indicate that the application process has not crashed. Kubernetes will use this to decide whether to restart the container.
- [ ] **Implement a Readiness Probe**: Create a `/health/ready` endpoint. This endpoint should perform a quick check on critical dependencies, such as the ability to connect to the database. It should only return `200 OK` if the application is fully initialized and ready to accept traffic. Kubernetes will use this to decide when to add the pod to the service load balancer.
- [ ] **Update Kubernetes Deployment**: Add `livenessProbe` and `readinessProbe` sections to the application's `Deployment` manifest, pointing to these new endpoints.

---

### 3. How might operations gain visibility into service health and performance?

**Answer:** Through a combination of **structured logging** and **application metrics**.

**TODO:**
- [ ] **Implement Structured Logging**: Integrate a library like `structlog` to output logs in a machine-readable format (JSON). This allows logs to be easily ingested, searched, and analyzed by log aggregation platforms like Elasticsearch, Loki, or Splunk.
- [ ] **Expose a Metrics Endpoint**: Use a library like `prometheus-fastapi-instrumentator` to automatically instrument the application and expose a `/metrics` endpoint compatible with Prometheus.
- [ ] **Define Key Metrics**: Track and expose key performance indicators (KPIs), such as:
    - Request latency and count per endpoint.
    - Error rates per endpoint.
    - Latency of calls to the external LLM API.
    - Number of tool calls performed.

---

### 4. What about persistent data in containerized deployments?

**Answer:** For stateful services like the PostgreSQL database, data must be stored outside the container's ephemeral filesystem using **persistent volumes**.

**TODO:**
- [ ] **Define a PersistentVolumeClaim (PVC)**: Create a `PersistentVolumeClaim` manifest (`k8s/pvc.yaml`). This requests storage from the Kubernetes cluster without needing to know the details of the underlying storage infrastructure.
- [ ] **Update Database Deployment**: The PostgreSQL database should be deployed as a `StatefulSet` rather than a `Deployment`. Update its manifest (`k8s/postgres.yaml`) to mount the storage defined by the PVC. This ensures that the database's data directory persists across pod restarts and rescheduling.
- [ ] **Document Backup/Restore Strategy**: Define and document the operational procedures for backing up and restoring the data stored in the persistent volume.

---

### 5. How would you handle TLS termination and port configuration?

**Answer:** TLS should be terminated at the edge of the cluster by an **Ingress Controller**, not by the application itself. The application's port should be configurable.

**TODO:**
- [ ] **Implement an Ingress Controller**: In a production Kubernetes cluster, an Ingress Controller (like NGINX) should be installed to manage external traffic.
- [ ] **Create an Ingress Manifest**: Define an `Ingress` resource (`k8s/ingress.yaml`). This manifest will configure the controller to:
    - Listen for external traffic (e.g., on port 443).
    - **Terminate TLS**: Handle the TLS handshake using a certificate (ideally managed by `cert-manager`).
    - Route decrypted HTTP traffic to the application's internal `ClusterIP` service.
- [ ] **Decouple Port Configuration**:
    - The application's internal port should be configurable via an environment variable (e.g., `PORT=8080`).
    - Update `uvicorn.run` in `main.py` to use this environment variable.
    - The `Dockerfile` should use `EXPOSE` to document this internal port. This decouples the port the application listens on internally from the port exposed to the outside world.
