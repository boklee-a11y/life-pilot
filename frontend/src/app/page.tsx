import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center pt-20 text-center">
      <h1 className="text-4xl font-bold leading-tight sm:text-5xl">
        데이터로 증명하고,
        <br />
        <span className="text-[var(--color-primary)]">액션으로 성장하는</span>
        <br />
        커리어 내비게이션
      </h1>

      <p className="mt-6 max-w-md text-lg text-[var(--muted-foreground)]">
        프로필 URL만 입력하면, AI가 당신의 커리어를 분석하고
        시장 가치를 측정합니다.
      </p>

      <Link
        href="/auth"
        className="mt-10 rounded-xl bg-[var(--color-primary)] px-8 py-4 text-lg font-semibold text-white shadow-lg transition hover:bg-[var(--color-primary-dark)] hover:shadow-xl"
      >
        30초 만에 분석하는 나의 시장 가치
      </Link>

      <div className="mt-16 grid w-full max-w-2xl grid-cols-1 gap-4 sm:grid-cols-3">
        {[
          { title: "URL 입력", desc: "LinkedIn, GitHub 등 프로필 URL만 붙여넣기" },
          { title: "AI 분석", desc: "5대 영역 스코어링 + 시장 가치 측정" },
          { title: "액션 추천", desc: "몸값을 높이는 맞춤 성장 전략 제안" },
        ].map((item, i) => (
          <div
            key={i}
            className="rounded-xl border border-[var(--border)] bg-[var(--card)] p-6 text-left"
          >
            <div className="mb-2 text-2xl font-bold text-[var(--color-primary)]">
              {i + 1}
            </div>
            <h3 className="font-semibold">{item.title}</h3>
            <p className="mt-1 text-sm text-[var(--muted-foreground)]">
              {item.desc}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
