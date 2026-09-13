import Link from "next/link";

/**
 * The front door, and nothing else.
 *
 * This used to be the author's workspace. The authoring screens are gone from the
 * browser, so the only thing a visitor can do here is answer a survey, and the page says
 * so rather than describing a product they cannot reach.
 */
export default function Home() {
  return (
    <div className="page narrow">
      <div className="page-head">
        <h1>Elenchus</h1>
      </div>
      <p>
        A survey you answer by talking. The engine decides which question is current and
        when you are finished; the model helps ask and record, and nothing it says is kept
        until it has been checked.
      </p>
      <div className="actions">
        <Link className="btn btn-primary" href="/respond">
          Answer a survey
        </Link>
      </div>
    </div>
  );
}
