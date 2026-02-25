'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import Disclaimer from '@/components/Disclaimer';
import { DailyEntry, MetricDefinition, fetchMetrics, fetchTodayEntry, upsertEntry } from '@/lib/api';

type ValueState = Record<string, number | string>;

export default function HomePage() {
  const [metrics, setMetrics] = useState<MetricDefinition[]>([]);
  const [entry, setEntry] = useState<DailyEntry | null>(null);
  const [values, setValues] = useState<ValueState>({});
  const [note, setNote] = useState('');
  const [error, setError] = useState('');
  const [saveState, setSaveState] = useState<'idle' | 'saving' | 'done'>('idle');

  useEffect(() => {
    if (!localStorage.getItem('access_token')) {
      window.location.href = '/login';
      return;
    }

    (async () => {
      try {
        const [metricData, today] = await Promise.all([fetchMetrics(), fetchTodayEntry()]);
        setMetrics(metricData);
        setEntry(today);
        setNote(today.note || '');

        const nextValues: ValueState = {};
        for (const metric of metricData) {
          const current = today.metric_values.find((v) => v.metric_key === metric.key);
          if (metric.input_type === 'scale') {
            nextValues[metric.key] = current?.value_int ?? 5;
          } else {
            nextValues[metric.key] = current?.value_text ?? '';
          }
        }
        setValues(nextValues);
      } catch {
        setError('불러오기 실패');
      }
    })();
  }, []);

  const date = useMemo(() => entry?.date ?? new Date().toISOString().slice(0, 10), [entry?.date]);

  const save = async () => {
    setSaveState('saving');
    setError('');

    try {
      await upsertEntry({
        date,
        note,
        values: metrics.map((metric) => {
          const current = values[metric.key];
          if (metric.input_type === 'scale') {
            return { metric_key: metric.key, value_int: Number(current) };
          }
          return { metric_key: metric.key, value_text: String(current || '') };
        }),
      });
      setSaveState('done');
      setTimeout(() => setSaveState('idle'), 1500);
    } catch {
      setError('저장 실패');
      setSaveState('idle');
    }
  };

  return (
    <section className="space-y-4">
      <header className="space-y-2">
        <h1 className="text-2xl font-bold">오늘 체크인</h1>
        <p className="text-sm text-slate-600">{date}</p>
        <Link href="/trend" className="inline-block rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-medium">
          추세 보기
        </Link>
      </header>

      <Disclaimer />

      {error && <p className="text-sm text-red-600">{error}</p>}

      <div className="space-y-4 rounded-xl bg-white p-4 shadow">
        {metrics.map((metric) => (
          <div key={metric.key} className="space-y-2">
            <label className="font-medium">{metric.name}</label>
            {metric.input_type === 'scale' ? (
              <>
                <input
                  type="range"
                  min={metric.min_value ?? 0}
                  max={metric.max_value ?? 10}
                  value={Number(values[metric.key] ?? 5)}
                  className="w-full"
                  onChange={(e) => setValues((prev) => ({ ...prev, [metric.key]: Number(e.target.value) }))}
                />
                <p className="text-right text-sm text-slate-600">{values[metric.key] ?? 5}</p>
              </>
            ) : (
              <input
                className="w-full rounded-lg border p-3"
                value={String(values[metric.key] ?? '')}
                onChange={(e) => setValues((prev) => ({ ...prev, [metric.key]: e.target.value }))}
                placeholder="예: 정상 / 무름 / 딱딱함"
              />
            )}
          </div>
        ))}

        <div className="space-y-2">
          <label className="font-medium">메모</label>
          <textarea className="w-full rounded-lg border p-3" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>

        <button onClick={save} className="w-full rounded-lg bg-blue-600 p-3 font-semibold text-white" disabled={saveState === 'saving'}>
          {saveState === 'saving' ? '저장 중...' : saveState === 'done' ? '저장 완료' : '저장'}
        </button>
      </div>
    </section>
  );
}
