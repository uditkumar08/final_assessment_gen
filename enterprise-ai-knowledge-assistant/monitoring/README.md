# Prometheus, Grafana, and Loki

Prometheus collects app metrics, Grafana displays metrics and logs, and Loki stores logs. A ServiceMonitor is a Kubernetes resource that tells Prometheus Operator which service to scrape.

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
kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80
```

Open Grafana at <http://localhost:3000>. Sign in as `admin`. To retrieve the generated password in PowerShell:

```powershell
$encoded = kubectl get secret monitoring-grafana -n monitoring -o 'jsonpath={.data.admin-password}'
[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded))
```

Forward Prometheus in another window:

```powershell
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090
```

Open Prometheus at <http://localhost:9090>. To open the Streamlit UI, forward its service:

```powershell
kubectl port-forward -n default svc/frontend-service 8501:8501
```

Then open <http://localhost:8501>.

## Configure Loki in Grafana

In Grafana, go to **Connections > Data sources > Add data source > Loki** and set the URL to:

```text
http://loki.monitoring.svc.cluster.local:3100
```

Save and test the data source.

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
{app="backend"}
```
