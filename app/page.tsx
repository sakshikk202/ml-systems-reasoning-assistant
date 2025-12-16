export default function Home() {
  return (
    <main style={{ padding: "40px", fontFamily: "Arial, sans-serif" }}>
      <h1>ML Systems Reasoning Assistant</h1>

      <p>
        This tool demonstrates how large language models can be used to reason
        about real-world ML system design decisions.
      </p>

      <ul>
        <li>Model selection trade-offs</li>
        <li>Latency vs accuracy decisions</li>
        <li>Infrastructure and scaling considerations</li>
        <li>Failure modes and observability</li>
      </ul>

      <p>
        This project is intentionally designed to be simple to evaluate and easy
        to reason about — no complex prompts required.
      </p>

      <button style={{ padding: "10px 16px", marginTop: "20px" }}>
        Try a Sample Question
      </button>
    </main>
  );
}
