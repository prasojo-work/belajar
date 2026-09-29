export default function Home() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center gap-4 bg-zinc-50 p-8 font-sans dark:bg-black">
      <h1 className="text-5xl font-semibold tracking-tight text-black dark:text-zinc-50">
        Hello World
      </h1>
      <p className="text-lg text-zinc-600 dark:text-zinc-400">
        Next.js + pnpm, deployed on Vercel.
      </p>
    </main>
  );
}
