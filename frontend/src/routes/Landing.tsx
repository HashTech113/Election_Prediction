import { Link } from "react-router-dom";
import { useEffect, useRef, useState } from "react";
import "../styles/landing.css";

export function Landing() {
  const [logoVideoDone, setLogoVideoDone] = useState(false);
  const [logoVideoVisible, setLogoVideoVisible] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  useEffect(() => {
    // Try to force-start playback for browsers that ignore autoplay
    // until JS explicitly calls play().
    void videoRef.current?.play().catch(() => undefined);
  }, []);

  useEffect(() => {
    // Safety fallback: if playback stalls, reveal the static logo.
    const timerId = window.setTimeout(() => {
      setLogoVideoVisible(false);
      setLogoVideoDone(true);
    }, 8000);
    return () => window.clearTimeout(timerId);
  }, []);

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
                  className="l-q-logo l-q-logo-static is-visible"
                  width={56}
                  height={56}
                  decoding="async"
                />
                <video
                  ref={videoRef}
                  className={`l-q-logo l-q-logo-video ${
                    !logoVideoDone && logoVideoVisible ? "is-visible" : "is-hidden"
                  }`}
                  width={56}
                  height={56}
                  autoPlay
                  muted
                  playsInline
                  preload="auto"
                  onCanPlay={() => {
                    void videoRef.current?.play().catch(() => undefined);
                  }}
                  onPlaying={() => setLogoVideoVisible(true)}
                  onEnded={() => {
                    setLogoVideoVisible(false);
                    setLogoVideoDone(true);
                  }}
                  onError={() => {
                    setLogoVideoVisible(false);
                    setLogoVideoDone(true);
                  }}
                >
                  <source src="/assets/logo_video.mp4" type="video/mp4" />
                </video>
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
                DMK Alliance, AIADMK+NDA, TVK, NTK, Others — historical
                projections plus long-term trend, recent swing &amp; live
                intelligence views.
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
                LDF, UDF, NDA, Others — model-driven 2026 projections with
                scenario overlays for alternative vote-shift outcomes.
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
