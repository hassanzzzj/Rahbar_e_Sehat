/**
 * Full-page skeleton shown while lazy-loaded routes are loading.
 * Uses skeleton screens (not spinners) per Master Build Prompt UI rules.
 */
export function SkeletonPage() {
  return (
    <section aria-busy="true" aria-label="Loading content" className="mx-auto max-w-3xl px-3 py-6">
      <div className="skeleton h-[5] w-2/3" />
      <div className="mt-3 skeleton h-[2] w-full" />
      <div className="mt-1 skeleton h-[2] w-5/6" />
      <div className="mt-4 grid grid-cols-1 gap-2 sm:grid-cols-2">
        <div className="skeleton h-[12] w-full" />
        <div className="skeleton h-[12] w-full" />
      </div>
    </section>
  );
}
