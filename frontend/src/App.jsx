import {
  AlertTriangle,
  CheckCircle2,
  Download,
  ExternalLink,
  FileJson,
  FileText,
  Loader2,
  SearchCheck,
  ShieldAlert,
  UploadCloud,
  XCircle,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { getReport, reportDownloadUrl, uploadPdf } from "./api";

const steps = ["Parsing PDF", "Extracting factual claims", "Verifying claims", "Generating reports"];

const statusStyles = {
  VERIFIED: {
    label: "Verified",
    icon: CheckCircle2,
    classes: "border-emerald-200 bg-emerald-50 text-emerald-800",
    dot: "bg-emerald-500",
  },
  OUTDATED: {
    label: "Outdated",
    icon: AlertTriangle,
    classes: "border-amber-200 bg-amber-50 text-amber-800",
    dot: "bg-amber-500",
  },
  INACCURATE: {
    label: "Inaccurate",
    icon: ShieldAlert,
    classes: "border-orange-200 bg-orange-50 text-orange-800",
    dot: "bg-orange-500",
  },
  FALSE: {
    label: "False",
    icon: XCircle,
    classes: "border-rose-200 bg-rose-50 text-rose-800",
    dot: "bg-rose-500",
  },
  "INSUFFICIENT EVIDENCE": {
    label: "Insufficient",
    icon: SearchCheck,
    classes: "border-slate-200 bg-slate-50 text-slate-700",
    dot: "bg-slate-400",
  },
  PENDING: {
    label: "Pending",
    icon: Loader2,
    classes: "border-slate-200 bg-white text-slate-600",
    dot: "bg-slate-300",
  },
};

function cx(...classes) {
  return classes.filter(Boolean).join(" ");
}

export default function App() {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [reportId, setReportId] = useState(null);
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [filter, setFilter] = useState("ALL");

  const isComplete = report?.status === "COMPLETED";
  const isFailed = report?.status === "FAILED";

  useEffect(() => {
    if (!reportId || isComplete || isFailed) return undefined;
    let active = true;
    const poll = async () => {
      try {
        const nextReport = await getReport(reportId);
        if (active) setReport(nextReport);
      } catch (pollError) {
        if (active) setError(pollError.message);
      }
    };
    poll();
    const timer = window.setInterval(poll, 2200);
    return () => {
      active = false;
      window.clearInterval(timer);
    };
  }, [reportId, isComplete, isFailed]);

  const filteredClaims = useMemo(() => {
    const claims = report?.claims || [];
    if (filter === "ALL") return claims;
    return claims.filter((claim) => claim.status === filter);
  }, [filter, report]);

  async function startUpload(selectedFile = file) {
    if (!selectedFile) {
      setError("Choose a PDF first.");
      return;
    }
    setError("");
    setIsUploading(true);
    try {
      const upload = await uploadPdf(selectedFile);
      setReportId(upload.id);
      setReport({
        id: upload.id,
        filename: selectedFile.name,
        status: upload.status,
        current_step: upload.current_step,
        progress: upload.progress,
        claims: [],
        summary: {},
      });
    } catch (uploadError) {
      setError(uploadError.message);
    } finally {
      setIsUploading(false);
    }
  }

  function onDrop(event) {
    event.preventDefault();
    setIsDragging(false);
    const selected = event.dataTransfer.files?.[0];
    if (selected) {
      setFile(selected);
      startUpload(selected);
    }
  }

  function resetFlow() {
    setFile(null);
    setReportId(null);
    setReport(null);
    setError("");
    setFilter("ALL");
  }

  return (
    <div className="min-h-screen bg-[#f6f8fb] text-slate-950">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-4">
          <button className="flex items-center gap-3" onClick={resetFlow} type="button">
            <span className="flex h-10 w-10 items-center justify-center rounded-md bg-slate-950 text-white">
              <SearchCheck size={22} />
            </span>
            <span className="text-left">
              <span className="block text-base font-semibold">Fact-Check Agent</span>
              <span className="block text-xs text-slate-500">PDF evidence verification</span>
            </span>
          </button>
          {reportId && (
            <button
              className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
              onClick={resetFlow}
              type="button"
            >
              New report
            </button>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-5 py-8">
        {!reportId && (
          <section className="grid gap-8 lg:grid-cols-[1fr_380px] lg:items-start">
            <div className="pt-4">
              <p className="mb-3 text-sm font-semibold uppercase tracking-[0.18em] text-teal-700">
                Evidence-first AI review
              </p>
              <h1 className="max-w-3xl text-4xl font-semibold leading-tight text-slate-950 md:text-5xl">
                Upload a PDF and verify every factual claim against live sources.
              </h1>
              <p className="mt-5 max-w-2xl text-base leading-7 text-slate-600">
                The agent extracts statistics, dates, market claims, revenue numbers, and technical figures,
                then builds a source-backed report with confidence scores.
              </p>
              <div className="mt-8 grid gap-3 sm:grid-cols-3">
                {[
                  ["PDF parsing", "PyMuPDF + pdfplumber"],
                  ["Live evidence", "Tavily, Serper, DuckDuckGo"],
                  ["Final reports", "PDF + JSON downloads"],
                ].map(([title, body]) => (
                  <div className="rounded-md border border-slate-200 bg-white p-4 shadow-sm" key={title}>
                    <p className="font-medium text-slate-900">{title}</p>
                    <p className="mt-1 text-sm text-slate-500">{body}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-md border border-slate-200 bg-white p-5 shadow-soft">
              <div
                className={cx(
                  "flex min-h-[290px] cursor-pointer flex-col items-center justify-center rounded-md border-2 border-dashed px-5 text-center transition",
                  isDragging ? "border-teal-500 bg-teal-50" : "border-slate-300 bg-slate-50 hover:bg-white",
                )}
                onClick={() => inputRef.current?.click()}
                onDragOver={(event) => {
                  event.preventDefault();
                  setIsDragging(true);
                }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={onDrop}
                role="button"
                tabIndex={0}
              >
                <UploadCloud className="mb-5 text-teal-700" size={46} />
                <p className="text-lg font-semibold text-slate-950">Drop a PDF here</p>
                <p className="mt-2 max-w-xs text-sm leading-6 text-slate-500">
                  Upload pitch decks, reports, whitepapers, or trap documents with fake statistics.
                </p>
                {file && <p className="mt-4 rounded-md bg-white px-3 py-2 text-sm text-slate-700">{file.name}</p>}
                <input
                  accept="application/pdf"
                  className="hidden"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                  ref={inputRef}
                  type="file"
                />
              </div>

              {error && <p className="mt-4 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}

              <button
                className="mt-5 flex w-full items-center justify-center gap-2 rounded-md bg-slate-950 px-4 py-3 font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
                disabled={!file || isUploading}
                onClick={() => startUpload()}
                type="button"
              >
                {isUploading ? <Loader2 className="animate-spin" size={18} /> : <UploadCloud size={18} />}
                {isUploading ? "Uploading" : "Analyze PDF"}
              </button>
            </div>
          </section>
        )}

        {reportId && !isComplete && (
          <ProcessingView error={error || report?.error} progress={report?.progress || 0} step={report?.current_step} />
        )}

        {isComplete && report && (
          <ResultsView
            claims={filteredClaims}
            filter={filter}
            report={report}
            setFilter={setFilter}
          />
        )}
      </main>
    </div>
  );
}

function ProcessingView({ error, progress, step }) {
  return (
    <section className="mx-auto max-w-3xl py-8">
      <div className="rounded-md border border-slate-200 bg-white p-6 shadow-soft">
        <div className="mb-6 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-semibold">Processing report</h2>
            <p className="mt-1 text-sm text-slate-500">{step || "Starting pipeline"}</p>
          </div>
          <Loader2 className="animate-spin text-teal-700" size={32} />
        </div>

        <div className="h-3 overflow-hidden rounded-full bg-slate-100">
          <div className="h-full rounded-full bg-teal-600 transition-all" style={{ width: `${progress}%` }} />
        </div>
        <p className="mt-2 text-right text-sm font-medium text-slate-600">{progress}%</p>

        <div className="mt-6 grid gap-3 sm:grid-cols-2">
          {steps.map((item) => {
            const active = (step || "").toLowerCase().includes(item.split(" ")[0].toLowerCase());
            return (
              <div
                className={cx(
                  "flex items-center gap-3 rounded-md border p-3",
                  active ? "border-teal-300 bg-teal-50 text-teal-900" : "border-slate-200 bg-slate-50 text-slate-600",
                )}
                key={item}
              >
                <span className={cx("h-2.5 w-2.5 rounded-full", active ? "bg-teal-600" : "bg-slate-300")} />
                <span className="text-sm font-medium">{item}</span>
              </div>
            );
          })}
        </div>

        {error && <p className="mt-5 rounded-md bg-rose-50 px-3 py-2 text-sm text-rose-700">{error}</p>}
      </div>
    </section>
  );
}

function ResultsView({ claims, filter, report, setFilter }) {
  const summary = report.summary || {};
  const filters = [
    ["ALL", "All", summary.total || 0],
    ["VERIFIED", "Verified", summary.verified || 0],
    ["OUTDATED", "Outdated", summary.outdated || 0],
    ["INACCURATE", "Inaccurate", summary.inaccurate || 0],
    ["FALSE", "False", summary.false || 0],
    ["INSUFFICIENT EVIDENCE", "Insufficient", summary.insufficient_evidence || 0],
  ];

  return (
    <section className="space-y-6">
      <div className="flex flex-col justify-between gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-end">
        <div>
          <p className="text-sm font-medium text-teal-700">Report complete</p>
          <h2 className="mt-1 text-3xl font-semibold">{report.filename}</h2>
          <p className="mt-2 text-sm text-slate-500">{summary.total || 0} extracted claims reviewed.</p>
        </div>
        <div className="flex flex-wrap gap-3">
          <a
            className="flex items-center gap-2 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-semibold text-slate-800 hover:bg-slate-100"
            href={reportDownloadUrl(report.id, "json")}
          >
            <FileJson size={17} />
            JSON
          </a>
          <a
            className="flex items-center gap-2 rounded-md bg-slate-950 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            href={reportDownloadUrl(report.id, "pdf")}
          >
            <Download size={17} />
            PDF report
          </a>
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <SummaryTile label="Verified" value={summary.verified || 0} tone="bg-emerald-50 text-emerald-800" />
        <SummaryTile label="Outdated" value={summary.outdated || 0} tone="bg-amber-50 text-amber-800" />
        <SummaryTile label="Inaccurate" value={summary.inaccurate || 0} tone="bg-orange-50 text-orange-800" />
        <SummaryTile label="False" value={summary.false || 0} tone="bg-rose-50 text-rose-800" />
        <SummaryTile
          label="Insufficient"
          value={summary.insufficient_evidence || 0}
          tone="bg-slate-100 text-slate-700"
        />
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {filters.map(([value, label, count]) => (
          <button
            className={cx(
              "whitespace-nowrap rounded-md border px-3 py-2 text-sm font-medium",
              filter === value
                ? "border-slate-950 bg-slate-950 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:bg-slate-100",
            )}
            key={value}
            onClick={() => setFilter(value)}
            type="button"
          >
            {label} · {count}
          </button>
        ))}
      </div>

      <div className="grid gap-4">
        {claims.map((claim) => (
          <ClaimCard claim={claim} key={claim.id || claim.claim} />
        ))}
        {claims.length === 0 && (
          <div className="rounded-md border border-slate-200 bg-white p-8 text-center text-slate-500">
            No claims match this filter.
          </div>
        )}
      </div>
    </section>
  );
}

function SummaryTile({ label, value, tone }) {
  return (
    <div className={cx("rounded-md border border-white p-4 shadow-sm", tone)}>
      <p className="text-3xl font-semibold">{value}</p>
      <p className="mt-1 text-sm font-medium">{label}</p>
    </div>
  );
}

function ClaimCard({ claim }) {
  const meta = statusStyles[claim.status] || statusStyles.PENDING;
  const Icon = meta.icon;

  return (
    <article className="rounded-md border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
        <div>
          <div className="mb-3 flex flex-wrap items-center gap-2">
            <span className={cx("inline-flex items-center gap-2 rounded-md border px-2.5 py-1 text-xs font-semibold", meta.classes)}>
              <Icon size={15} />
              {meta.label}
            </span>
            <span className="rounded-md bg-slate-100 px-2.5 py-1 text-xs font-medium uppercase text-slate-500">
              {claim.claim_type || claim.type || "general"}
            </span>
            {claim.page && <span className="text-xs text-slate-500">Page {claim.page}</span>}
          </div>
          <h3 className="text-lg font-semibold leading-7 text-slate-950">{claim.claim}</h3>
          {claim.explanation && <p className="mt-3 text-sm leading-6 text-slate-600">{claim.explanation}</p>}
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 px-4 py-3 text-center md:min-w-28">
          <p className="text-2xl font-semibold text-slate-950">{claim.confidence || 0}%</p>
          <p className="text-xs font-medium text-slate-500">confidence</p>
        </div>
      </div>

      {claim.correct_value && (
        <div className="mt-4 rounded-md border border-teal-200 bg-teal-50 p-3 text-sm text-teal-900">
          <span className="font-semibold">Correct fact: </span>
          {claim.correct_value}
        </div>
      )}

      {claim.evidence?.length > 0 && (
        <div className="mt-5">
          <div className="mb-2 flex items-center gap-2 text-sm font-semibold text-slate-700">
            <FileText size={16} />
            Evidence links
          </div>
          <div className="grid gap-2">
            {claim.evidence.slice(0, 5).map((source) => (
              <a
                className="flex items-start justify-between gap-3 rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm hover:bg-white"
                href={source.url}
                key={source.url}
                rel="noreferrer"
                target="_blank"
              >
                <span>
                  <span className="block font-medium text-slate-800">{source.title}</span>
                  <span className="mt-1 block text-xs uppercase text-slate-500">{source.source_type}</span>
                </span>
                <ExternalLink className="mt-1 shrink-0 text-slate-400" size={16} />
              </a>
            ))}
          </div>
        </div>
      )}
    </article>
  );
}

