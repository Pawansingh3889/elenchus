/**
 * The matrix as a spreadsheet.
 *
 * Built in the browser from data the page already has, because the matrix *is* the
 * export: one row per response, one column per question. There was no export at all
 * before, and the answer to "I need this in a spreadsheet" was to open each response in
 * turn and retype it.
 *
 * Follow-ups get their own columns rather than being folded into the answer beside
 * them, on the same rule the tallies use: a follow-up answers a question the model
 * wrote, and merging it would credit the author's question with words it never asked.
 */
import type { Messages } from "@/lib/i18n";
import type { AnswersMatrix, MatrixRun } from "@/lib/types";
import { readAnswer } from "@/lib/answers";

/** RFC 4180 quoting: double the quotes, wrap anything holding a comma, quote or newline.
 *
 *  The leading-character guard is not decoration. A cell beginning =, +, - or @ is run
 *  as a formula by Excel and Sheets when the file is opened, so a respondent's free text
 *  is a script injected into whoever opens the export. Prefixing a tab neutralises it
 *  and still reads as the words they wrote. */
function cell(value: string): string {
  const guarded = /^[=+\-@\t\r]/.test(value) ? `\t${value}` : value;
  return /[",\n\r]/.test(guarded) ? `"${guarded.replace(/"/g, '""')}"` : guarded;
}

export function matrixToCsv(matrix: AnswersMatrix, runs: MatrixRun[], msg: Messages): string {
  const questions = [...matrix.questions].sort((a, b) => a.position - b.position);
  const header = [
    msg.results.tableRespondent,
    msg.results.tableStatus,
    msg.results.tableFinished,
    ...questions.flatMap((q) => [q.text, `${q.text} (${msg.results.followUp})`]),
  ];

  const rows = runs.map((run) => {
    const byQuestion = new Map<string, { scripted?: string; probes: string[] }>();
    for (const answer of run.answers) {
      if (!byQuestion.has(answer.question_id)) byQuestion.set(answer.question_id, { probes: [] });
      const slot = byQuestion.get(answer.question_id)!;
      if (answer.kind === "scripted") slot.scripted = readAnswer(answer.value, msg);
      else slot.probes.push(readAnswer(answer.value, msg));
    }
    return [
      run.respondent_label,
      run.status === "completed" ? msg.results.statusComplete : msg.results.statusInProgress,
      run.completed_at ? new Date(run.completed_at).toISOString() : "",
      ...questions.flatMap((q) => {
        const slot = byQuestion.get(q.id);
        return [slot?.scripted ?? "", (slot?.probes ?? []).join(" | ")];
      }),
    ];
  });

  return [header, ...rows].map((row) => row.map(cell).join(",")).join("\r\n");
}

/** Hand the file to the browser. A blob and a synthetic click, because there is no
 *  server route to link to and building one would put a spreadsheet renderer in the API
 *  for something the client can already do. */
export function downloadCsv(filename: string, contents: string): void {
  // The BOM is what makes Excel read UTF-8 rather than the local codepage, which is the
  // difference between a Latvian answer arriving intact and arriving as mojibake.
  const blob = new Blob(["﻿", contents], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
