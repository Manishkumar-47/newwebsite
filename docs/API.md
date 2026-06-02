# API Documentation

Base URL for local development: `http://localhost:8000`

## GET /health

Returns service status.

```json
{
  "status": "ok",
  "service": "fact-check-agent"
}
```

## POST /upload

Uploads a PDF, creates a report job, and starts background processing.

Request: multipart form data

| Field | Type | Required |
| ----- | ---- | -------- |
| file | PDF file | yes |

Response:

```json
{
  "id": "report-uuid",
  "status": "QUEUED",
  "current_step": "Queued",
  "progress": 0
}
```

Poll `GET /report/{id}` until `status` is `COMPLETED` or `FAILED`.

## POST /extract-claims

Extracts claims from a PDF without creating a report job.

Request: multipart form data with `file`.

Response:

```json
{
  "claims": [
    {
      "claim": "India has 900 million internet users.",
      "type": "statistic",
      "page": 1
    }
  ],
  "character_count": 812,
  "page_count": 3
}
```

## POST /verify

Verifies supplied claims without uploading a PDF.

Request:

```json
{
  "claims": [
    {
      "claim": "ChatGPT launched in 2018.",
      "type": "date"
    }
  ]
}
```

Response:

```json
{
  "results": [
    {
      "claim": "ChatGPT launched in 2018.",
      "type": "date",
      "status": "FALSE",
      "confidence": 96,
      "correct_value": "ChatGPT launched publicly on November 30, 2022.",
      "explanation": "The claim gives an impossible launch year for ChatGPT; the public launch was in 2022.",
      "sources": []
    }
  ]
}
```

## GET /report/{id}

Returns report progress and final claim data.

Statuses:

- `QUEUED`
- `PROCESSING`
- `COMPLETED`
- `FAILED`

Claim statuses:

- `VERIFIED`
- `OUTDATED`
- `INACCURATE`
- `FALSE`
- `INSUFFICIENT EVIDENCE`
- `PENDING`

## GET /report/{id}/download/json

Downloads the final JSON report. Available only after completion.

## GET /report/{id}/download/pdf

Downloads the final PDF report. Available only after completion.

