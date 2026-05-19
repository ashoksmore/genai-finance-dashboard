import { useCallback, useEffect, useState } from 'react'
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { getApiBase, getKpis, postExplain, uploadLedger } from './api'
import './App.css'

const money = new Intl.NumberFormat('en-US', {
  style: 'currency',
  currency: 'USD',
  maximumFractionDigits: 0,
})

function statusBadgeClass(status) {
  const key = String(status).replace(/-/g, '_')
  return `badge badge-${key}`
}

export default function App() {
  const [period, setPeriod] = useState('2025')
  const [payload, setPayload] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [loading, setLoading] = useState(true)

  const [uploadBusy, setUploadBusy] = useState(false)
  const [uploadMsg, setUploadMsg] = useState(null)

  const [question, setQuestion] = useState(
    'Are we on track to hit budget this year?',
  )
  const [explainBusy, setExplainBusy] = useState(false)
  const [explainBlock, setExplainBlock] = useState(null)

  const refresh = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const data = await getKpis(period)
      setPayload(data)
    } catch (e) {
      setPayload(null)
      setLoadError(e.message || String(e))
    } finally {
      setLoading(false)
    }
  }, [period])

  useEffect(() => {
    refresh()
  }, [refresh])

  async function onUpload(ev) {
    const file = ev.target.files?.[0]
    ev.target.value = ''
    if (!file) return
    setUploadBusy(true)
    setUploadMsg(null)
    try {
      const res = await uploadLedger(file)
      setUploadMsg(
        `Uploaded ${res.inserted_rows} rows for ${res.period}. Blob: ${res.blob_name}`,
      )
      await refresh()
    } catch (e) {
      setUploadMsg(`Upload failed: ${e.message}`)
    } finally {
      setUploadBusy(false)
    }
  }

  async function onExplain() {
    setExplainBusy(true)
    setExplainBlock(null)
    try {
      const { ok, data } = await postExplain(question.trim() || question)
      const answer = data.answer ?? data.detail ?? JSON.stringify(data)
      const err = data.error ? `\n\n(${data.error})` : ''
      setExplainBlock({
        ok,
        text: `${answer}${err}`,
        facts: data.facts_snapshot,
      })
    } catch (e) {
      setExplainBlock({ ok: false, text: e.message || String(e), facts: null })
    } finally {
      setExplainBusy(false)
    }
  }

  const kpis = payload?.kpis
  const forecast = payload?.forecast
  const trend = kpis?.monthly_trend ?? []
  const depts = kpis?.dept_summary ?? []
  const overruns = kpis?.overruns ?? []

  return (
    <div className="dashboard">
      <header className="dashboard-header">
        <div>
          <h1>Finance Health Dashboard</h1>
          <p className="subtle">
            API: <code>{getApiBase()}</code>
          </p>
        </div>
        {payload?.generated_at && (
          <p className="subtle">Updated {payload.generated_at}</p>
        )}
      </header>

      <div className="period-row">
        <label htmlFor="period">Report period (query)</label>
        <input
          id="period"
          value={period}
          onChange={(e) => setPeriod(e.target.value)}
        />
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => refresh()}
          disabled={loading}
        >
          {loading ? 'Loading…' : 'Refresh KPIs'}
        </button>
        <label className="btn btn-secondary" style={{ cursor: 'pointer' }}>
          {uploadBusy ? 'Uploading…' : 'Upload CSV'}
          <input
            type="file"
            accept=".csv,text/csv"
            hidden
            disabled={uploadBusy}
            onChange={onUpload}
          />
        </label>
      </div>

      {loadError && (
        <div className="alert alert-error">
          Could not load KPIs: {loadError}
        </div>
      )}

      {uploadMsg && (
        <div
          className={`alert ${uploadMsg.startsWith('Upload failed') ? 'alert-error' : 'alert-info'}`}
        >
          {uploadMsg}
        </div>
      )}

      {!loading && !kpis && !loadError && (
        <div className="alert alert-info">
          No ledger data yet. Upload a CSV (same columns as{' '}
          <code>sample_data.csv</code>) to populate the dashboard.
        </div>
      )}

      {kpis && (
        <>
          <section className="kpi-grid">
            <div className="kpi-card">
              <div className="label">Total budget</div>
              <div className="value">{money.format(kpis.total_budget)}</div>
            </div>
            <div className="kpi-card">
              <div className="label">Total actual</div>
              <div className="value">{money.format(kpis.total_actual)}</div>
            </div>
            <div className="kpi-card">
              <div className="label">Variance %</div>
              <div className="value">{kpis.variance_pct}%</div>
            </div>
            <div className="kpi-card">
              <div className="label">Forecast overrun</div>
              <div className="value">
                {forecast
                  ? money.format(forecast.forecast_overrun)
                  : '—'}
              </div>
            </div>
          </section>

          {forecast && (
            <section className="panel">
              <h2>Linear forecast (MVP)</h2>
              <p className="subtle" style={{ marginBottom: '0.75rem' }}>
                Projected EOY:{' '}
                <strong>{money.format(forecast.projected_eoy)}</strong>
                {' · '}
                Annualized budget:{' '}
                <strong>{money.format(forecast.full_year_budget)}</strong>
                {' · '}
                Avg monthly burn (3-mo):{' '}
                <strong>{money.format(forecast.avg_monthly_burn)}</strong>
                {' · '}
                Months remaining (model): {forecast.months_remaining}
              </p>
            </section>
          )}

          <section className="panel">
            <h2>Budget vs actual by month</h2>
            <div className="chart-wrap">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={trend} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#30363d" />
                  <XAxis dataKey="period" stroke="#8b949e" fontSize={12} />
                  <YAxis
                    stroke="#8b949e"
                    fontSize={12}
                    tickFormatter={(v) =>
                      v >= 1e6 ? `${(v / 1e6).toFixed(1)}M` : `${(v / 1000).toFixed(0)}k`
                    }
                  />
                  <Tooltip
                    formatter={(value) => money.format(value)}
                    contentStyle={{
                      background: '#161b22',
                      border: '1px solid #30363d',
                      borderRadius: 8,
                    }}
                  />
                  <Legend />
                  <Line type="monotone" dataKey="budget" stroke="#58a6ff" strokeWidth={2} dot={false} name="Budget" />
                  <Line type="monotone" dataKey="actual" stroke="#f78166" strokeWidth={2} dot={false} name="Actual" />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="panel">
            <h2>By department</h2>
            <table className="dept">
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Budget</th>
                  <th>Actual</th>
                  <th>Var %</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {depts.map((d) => (
                  <tr key={d.department}>
                    <td>{d.department}</td>
                    <td>{money.format(d.budget)}</td>
                    <td>{money.format(d.actual)}</td>
                    <td>{d.variance_pct}%</td>
                    <td>
                      <span className={statusBadgeClass(d.status)}>
                        {d.status.replace(/_/g, ' ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </section>

          {overruns.length > 0 && (
            <section className="panel">
              <h2>Overruns (&gt; 10% over budget)</h2>
              <ul style={{ margin: 0, paddingLeft: '1.2rem' }}>
                {overruns.map((d) => (
                  <li key={d.department}>
                    <strong>{d.department}</strong> — {d.variance_pct}% (
                    {money.format(d.variance)} over budget)
                  </li>
                ))}
              </ul>
            </section>
          )}

          <section className="panel">
            <h2>Ask the analyst (Azure OpenAI)</h2>
            <p className="subtle">
              Answers are grounded on KPI snapshots only (no raw ledger in the
              prompt).
            </p>
            <div className="explain-row">
              <textarea
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="Your question…"
              />
              <button
                type="button"
                className="btn"
                disabled={explainBusy}
                onClick={onExplain}
              >
                {explainBusy ? 'Thinking…' : 'Ask'}
              </button>
            </div>
            {explainBlock && (
              <>
                <div className="answer-box">{explainBlock.text}</div>
                {explainBlock.facts && (
                  <p className="facts-hint">
                    Response used deterministic KPI snapshot (totals, trends,
                    departments).
                  </p>
                )}
              </>
            )}
          </section>
        </>
      )}
    </div>
  )
}
