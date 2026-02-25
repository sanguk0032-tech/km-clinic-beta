'use client';

import { FormEvent, useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = await login(username, password);
      localStorage.setItem('access_token', data.access);
      router.push('/');
    } catch {
      setError('로그인에 실패했습니다. 아이디/비밀번호를 확인하세요.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="space-y-4">
      <h1 className="text-2xl font-bold">로그인</h1>
      <form onSubmit={onSubmit} className="space-y-3 rounded-xl bg-white p-4 shadow">
        <input
          className="w-full rounded-lg border p-3"
          placeholder="Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          required
        />
        <input
          className="w-full rounded-lg border p-3"
          placeholder="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button className="w-full rounded-lg bg-blue-600 p-3 font-semibold text-white" disabled={loading}>
          {loading ? '로그인 중...' : '로그인'}
        </button>
      </form>
    </section>
  );
}
