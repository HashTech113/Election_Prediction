import { ReactNode, useMemo } from "react";
import { LensName, LensSummary } from "../types/prediction";
import { asPercent } from "../utils/format";

const TABS: Array<{ label: string; lens: LensName }> = [
  { label: "HISTORICAL PROJECTION",  lens: "historical_projection" },
  { label: "LONG-TERM TREND",         lens: "long_term_trend" },
  { label: "RECENT SWING",            lens: "recent_swing" },
  { label: "LIVE INTELLIGENCE SCORE", lens: "final_prediction" },
];

interface AnalysisHeroProps {
  activeLens: LensName;
  onLensChange: (lens: LensName) => void;
  summaries: Partial<Record<LensName, LensSummary>>;
}

const PLACEHOLDER_NUM = "—";
const HEADING_STAGGER_MS = 70;
const VALUE_STAGGER_MS = 70;
const VALUE_HEAD_OFFSET_MS = 120;

export function AnalysisHero({ activeLens, onLensChange, summaries }: AnalysisHeroProps) {
  const summary = summaries[activeLens];

  const kpi = useMemo(
    () => [
      {
        label: "TOTAL CONSTITUENCIES",
        value: summary ? String(summary.total_constituencies) : PLACEHOLDER_NUM,
      },
      {
        label: "DATA REFERENCE",
        value: summary?.data_reference ?? PLACEHOLDER_NUM,
      },
      {
        label: "PROJECTED WINNER",
        value: summary?.projected_winner ?? PLACEHOLDER_NUM,
      },
      {
        label: "AVERAGE WINNING SCORE",
        value:
          !summary || summary.average_score === null
            ? PLACEHOLDER_NUM
            : asPercent(summary.average_score),
      },
    ],
    [summary],
  );

  return (
    <section className="ep-section">
      <header className="ep-hero">
        <div className="ep-brand">
          <img
            src="/assets/owlytics.png"
            alt="Owlytics logo"
            className="ep-logo"
            width={56}
            height={56}
            decoding="async"
          />
          <h1>Election Prediction</h1>
        </div>
        <p>
          Our <span>Intelligent AI</span> tracked every vote across{" "}
          <span>Kerala&apos;s</span> constituencies, uncovered key trends, and predicted who will
          form the next government.
        </p>
      </header>

      <nav className="ep-tabs" aria-label="Prediction analysis tabs">
        {TABS.map((tab) => (
          <button
            key={tab.lens}
            className={`ep-tab ${activeLens === tab.lens ? "active" : ""}`}
            onClick={() => onLensChange(tab.lens)}
            type="button"
            aria-pressed={activeLens === tab.lens}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <section className="ep-kpi">
        {kpi.map((item, i) => (
          <article key={item.label} className="ep-kpi-item">
            <h3>
              <span className="kpi-roll-box">
                <span
                  className="kpi-roll-text"
                  key={`h-${i}-${item.label}`}
                  style={{ ["--kpi-roll-delay" as string]: `${i * HEADING_STAGGER_MS}ms` }}
                >
                  {item.label}
                </span>
              </span>
            </h3>
            <strong aria-live="polite">
              <span className="kpi-roll-box">
                <span
                  className="kpi-roll-text"
                  key={`v-${i}-${activeLens}-${stringifyValue(item.value)}`}
                  style={{
                    ["--kpi-roll-delay" as string]:
                      `${VALUE_HEAD_OFFSET_MS + i * VALUE_STAGGER_MS}ms`,
                  }}
                >
                  {item.value}
                </span>
              </span>
            </strong>
          </article>
        ))}
      </section>
    </section>
  );
}

function stringifyValue(v: ReactNode): string {
  if (typeof v === "string" || typeof v === "number") return String(v);
  return "";
}
