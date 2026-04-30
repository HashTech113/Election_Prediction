import { Link } from "react-router-dom";
import "../styles/landing.css";

export function Landing() {
  return (
    <div className="landing-page">
      <div className="l-bg-blur l-bg-blur-a" />
      <div className="l-bg-blur l-bg-blur-b" />

      <main className="l-container">
        <header className="l-hero">
          <div className="l-hero-inner">
            <div className="l-brand-line" aria-label="Election Prediction">
              <span className="l-logo-stage" aria-hidden="true">
                <img
                  src="/assets/owlytics.png"
                  alt="Owlytics logo"
                  className="l-q-logo"
                  width={56}
                  height={56}
                  decoding="async"
                />
              </span>
              <h1 className="l-brand-title">Election Prediction</h1>
            </div>
            <p className="l-hero-tagline">
              Choose a state to explore <span className="l-accent">AI-led</span>{" "}
              constituency-level projections for the{" "}
              <span className="l-accent">2026 Assembly Elections</span>, powered by real-time
              insights and historical data intelligence.
            </p>
          </div>
        </header>

        <section className="l-state-grid" aria-label="Choose a state">
          <Link to="/tamilnadu" className="l-state-card l-state-tn" data-state="tamilnadu">
            <div className="l-state-card-inner">
              <div className="l-state-flag" aria-hidden="true">
                <span className="l-dot l-dot-dmk" />
                <span className="l-dot l-dot-aiadmk" />
                <span className="l-dot l-dot-tvk" />
                <span className="l-dot l-dot-others" />
              </div>
              <h2 className="l-state-name">Tamil Nadu</h2>
              <p className="l-state-meta">234 Constituencies · 38 Districts</p>
              <p className="l-state-desc">
                <strong>DMK Alliance, AIADMK+NDA, TVK, NTK</strong> — AI-driven constituency
                projections for Tamil Nadu with historical trends, voter swings, and real-time
                insights.
              </p>
              <span className="l-state-cta">
                Open Tamil Nadu Dashboard
                <span className="l-cta-arrow" aria-hidden="true">→</span>
              </span>
            </div>
          </Link>

          <Link to="/kerala" className="l-state-card l-state-kl" data-state="kerala">
            <div className="l-state-card-inner">
              <div className="l-state-flag" aria-hidden="true">
                <span className="l-dot l-dot-ldf" />
                <span className="l-dot l-dot-udf" />
                <span className="l-dot l-dot-nda" />
                <span className="l-dot l-dot-others" />
              </div>
              <h2 className="l-state-name">Kerala</h2>
              <p className="l-state-meta">140 Constituencies · 14 Districts</p>
              <p className="l-state-desc">
                <strong>LDF, UDF, NDA</strong> — AI-driven constituency projections for Kerala
                with historical trends, voter swings, and real-time insights.
              </p>
              <span className="l-state-cta">
                Open Kerala Dashboard
                <span className="l-cta-arrow" aria-hidden="true">→</span>
              </span>
            </div>
          </Link>
        </section>
      </main>
    </div>
  );
}
