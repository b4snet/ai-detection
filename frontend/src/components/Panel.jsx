export default function Panel({ title, children, className = '', right }) {
  return (
    <section className={`panel corner-frame p-4 md:p-5 ${className}`}>
      <header className="flex items-center justify-between mb-4 border-b border-sentinel-border/70 pb-2">
        <h2 className="panel-title">{title}</h2>
        {right}
      </header>
      {children}
    </section>
  )
}
