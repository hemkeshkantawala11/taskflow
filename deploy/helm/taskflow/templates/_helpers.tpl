{{- define "taskflow.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "taskflow.dbname" -}}
{{- printf "%s-postgres" (include "taskflow.fullname" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "taskflow.labels" -}}
app.kubernetes.io/part-of: taskflow
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end -}}

{{- define "taskflow.appSelector" -}}
app.kubernetes.io/name: taskflow
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: web
{{- end -}}

{{- define "taskflow.dbSelector" -}}
app.kubernetes.io/name: taskflow
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/component: database
{{- end -}}

{{- define "taskflow.image" -}}
{{- if not .Values.image.tag -}}
{{- fail "image.tag must be set (CI sets it to the git SHA in values-local.yaml)" -}}
{{- end -}}
{{- printf "%s:%s" .Values.image.repository .Values.image.tag -}}
{{- end -}}

{{/* Restricted Pod Security Standard: shared container hardening */}}
{{- define "taskflow.containerSecurity" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end -}}
