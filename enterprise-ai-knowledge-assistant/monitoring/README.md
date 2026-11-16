# Prometheus, Grafana, and Loki

Prometheus collects app metrics, Grafana displays metrics and logs, and Loki stores logs. A ServiceMonitor is a Kubernetes resource that tells Prometheus Operator which service to scrape.

This guide covers the Kubernetes monitoring stack. The standalone Prometheus service in Docker Compose is available at <http://localhost:9091>; the Kubernetes Prometheus port-forward below uses port 9090.

## Install the monitoring stack

These commands change Helm configuration and install resources into the Kubernetes cluster. Run them only after approving the install. If Helm was installed under `%LOCALAPPDATA%\Programs\Helm` and is not on `PATH`, add it to the current PowerShell session:

```powershell
$env:Path = "$env:LOCALAPPDATA\Programs\Helm;$env:Path"
```

```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
kubectl create namespace monitoring
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring
helm install loki grafana/loki-stack -n monitoring --set promtail.enabled=true --set grafana.enabled=false --set loki.isDefault=false
```

If the `monitoring` namespace already exists, skip its `kubectl create namespace` command. After the chart installs the ServiceMonitor CRD, apply the backend monitor:

```powershell
kubectl apply -f k8s/servicemonitor.yaml
```

The GitHub Actions deploy job applies this file automatically when the CRD is available.

## Open the dashboards

Run each port-forward in a separate PowerShell window and leave it running.

```powershell
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

Open Grafana at <http://localhost:3001> and sign in with the credentials stored in the `monitoring-grafana` Secret. Do not print the password or place it in a command, manifest, or repository file.

Forward Prometheus in another window:

```powershell
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open Prometheus at <http://localhost:9090>. To open the Streamlit UI, forward its service:

```powershell
kubectl port-forward -n default svc/frontend-service 8501:8501
```

Then open <http://localhost:8501>.

## Import the backend dashboard

The ready-to-import dashboard is [`grafana-dashboard.json`](./grafana-dashboard.json). In Grafana, select **Dashboards > New > Import**, choose **Upload JSON file**, select this file, then choose the Prometheus and Loki data sources from the dashboard variables and click **Import**. The dashboard uses datasource variables, so it is not tied to one Grafana instance's datasource UIDs.

The dashboard has panels for backend availability, request total/rate, p95 latency, 5xx rate, backend memory, and backend/frontend logs. The memory query uses the empty `container` label returned by Minikube's pod-level `container_memory_working_set_bytes` series. The 5xx panel displays zero until an error series exists.

To confirm the scrape target, open Prometheus at <http://localhost:9090>, select **Status > Targets**, and check that `backend-service` is **UP**. In the Prometheus query page, run:

```promql
up{job=~".*backend.*"}
```

Forward the backend service in another PowerShell window:

```powershell
kubectl port-forward -n default svc/backend-service 18000:8000
```

For backend metrics, open <http://localhost:18000/metrics>. To create sample metrics without uploading a document, use this PowerShell loop:

```powershell
1..15 | ForEach-Object {
  Invoke-WebRequest -UseBasicParsing http://localhost:18000/health | Out-Null
  Invoke-WebRequest -UseBasicParsing http://localhost:18000/ | Out-Null
}
```

Both requests are read-only and do not upload or process documents. The root route currently returns HTTP 200.

## Grafana dashboard and Loki logs

Applying `k8s/grafana-datasource.yaml` provisions the **Enterprise Loki** data source, and `k8s/grafana-dashboard.yaml` provisions the **Enterprise AI Knowledge Assistant** dashboard. The separate importable `grafana-dashboard.json` provides request totals/rates, p95 latency, 5xx rate, backend availability and memory, plus backend/frontend logs. The importable dashboard lets you choose Prometheus and Loki data sources from variables.

The Loki service is available to Grafana inside the cluster at:

```text
http://loki.monitoring.svc.cluster.local:3100
```

In Grafana, open **Dashboards > Enterprise AI Knowledge Assistant**. To explore logs directly, select the **Enterprise Loki** data source in **Explore** and query:

## Example queries

In Grafana **Explore**, select Prometheus for the first two queries and Loki for the third.

Backend request rate over five minutes:

```promql
sum(rate(http_requests_total{namespace="default",service="backend-service"}[5m]))
```

Backend 95th-percentile request latency over five minutes:

```promql
histogram_quantile(
  0.95,
  sum by (le) (
    rate(http_request_duration_seconds_bucket{namespace="default",service="backend-service"}[5m])
  )
)
```

Backend logs:

```logql
{app="backend", namespace="default"}
```

Frontend logs:

```logql
{app="frontend", namespace="default"}
```

For a direct Loki API check, forward the service:

```powershell
kubectl port-forward -n monitoring svc/loki 3100:3100
```

Then count recent backend log streams without printing log contents:

```powershell
$selector = [uri]::EscapeDataString('{app="backend",namespace="default"}')
$end = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
$start = $end - 3600
$result = Invoke-RestMethod "http://localhost:3100/loki/api/v1/query_range?query=$selector&start=$start&end=$end&limit=5"
"Backend log streams: $($result.data.result.Count)"
```

In Grafana, **Explore > Enterprise Loki > Label browser** shows available labels. Loki stores logs, while Prometheus stores numeric metrics; a log panel stays empty until the matching pod emits logs.
```
