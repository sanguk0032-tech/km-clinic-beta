'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import Disclaimer from '@/components/Disclaimer';
import { MetricDefinition, fetchMetrics, fetchTrend } from '@/lib/api';

export default function TrendPage() {
  const [metrics, setMetrics] = useState<MetricDefinition[]>([]);
  const [metricKey, setMetricKey] = useState('sleep_quality');
  const [days, setDays] = useState(30);
  const [points, setPoints] = useState<Array<{ date: string; value: number | string }>>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      window.location.href = '/login';
      return;
    }
    fetchMetrics().then((m) => {
      setMetrics(m);
      if (m.length > 0) setMetricKey(m[0].key);
    }).catch(() => setError('불러오기 실패'));
  }, []);

  useEffect(() => {
    if (!metricKey) return;
    fetchTrend(days, metricKey)
      .then((res) => {
        setPoints(res.points);
        setError('');
      })
      .catch(() => setError('불러오기 실패'));
  }, [days, metricKey]);

  const numericPoints = useMemo(
    () => points.filter((p) => typeof p.value === 'number').map((p) => ({ ...p, value: Number(p.value) })),
    [points],
  );

  const selectedMetric = metrics.find((m) => m.key === metricKey);

  return (
    <section className="space-y-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">추세</h1>
        <Link href="/" className="inline-block rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium">오늘 입력으로</Link>
      </header>

      <Disclaimer />

      <div className="rounded-xl bg-white p-4 shadow space-y-3">
        <div className="grid grid-cols-2 gap-3">
          <select className="rounded-lg border p-3" value={metricKey} onChange={(e) => setMetricKey(e.target.value)}>
            {metrics.map((metric) => (
              <option key={metric.key} value={metric.key}>{metric.name}</option>
            ))}
          </select>
          <select className="rounded-lg border p-3" value={days} onChange={(e) => setDays(Number(e.target.value))}>
            <option value={7}>7일</option>
            <option value={30}>30일</option>
            <option value={90}>90일</option>
          </select>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        {selectedMetric?.input_type === 'scale' ? (
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={numericPoints}>
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 10]} />
                <Tooltip />
                <Line dataKey="value" type="monotone" stroke="#2563eb" strokeWidth={2} dot />
              </LineChart>
            </ResponsiveContainer>
          </div>
        ) : (
          <ul className="space-y-2">
            {points.map((point) => (
              <li key={point.date} className="flex justify-between rounded-lg border p-2 text-sm">
                <span>{point.date}</span>
                <span>{String(point.value)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
