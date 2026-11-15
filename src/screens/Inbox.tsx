export function Inbox() {
  return <div className="page"><header className="page-header"><div><p className="eyebrow">Capture something delicious</p><h1>Recipe Inbox</h1><p>Save it now, review the details when you’re ready.</p></div></header>
    <div className="import-grid"><button><span>↗</span><div><h2>From a Link</h2><p>Paste a recipe page or video link</p></div></button><button><span>▧</span><div><h2>From a Photo</h2><p>Cookbook pages or handwritten cards</p></div></button></div>
    <section className="queue"><div className="section-heading"><div><p className="eyebrow">Saved for review</p><h2>Inbox Queue</h2></div><button className="text-button">View all</button></div>
      <article><div className="queue-thumb">▤</div><div><span className="queue-status review">Needs Review</span><h3>Mom’s Blueberry Cobbler</h3><p>2 cookbook photos · Added yesterday</p></div><button className="secondary">Review</button></article>
      <article><div className="queue-thumb">↗</div><div><span className="queue-status pending">Pending</span><h3>Weeknight sesame noodles</h3><p>Recipe link · Added today</p></div><button className="secondary">Open</button></article>
    </section>
  </div>
}
