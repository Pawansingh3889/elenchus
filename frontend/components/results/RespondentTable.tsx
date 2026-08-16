"use client";

import { Download } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { readAnswer } from "@/lib/answers";
import { downloadCsv, matrixToCsv } from "@/lib/csv";
import { useT } from "@/lib/i18n/useT";
import type { AnswersMatrix, MatrixRun } from "@/lib/types";

/**
 * Every response as one grid: respondents down, questions across.
 *
 * This is the view the app did not have. Responses showed one person at a time, so
 * comparing two meant remembering the first, and comparing eight meant a spreadsheet
 * the author built by hand. Reading down a column is how a pattern in one question
 * becomes visible; reading across a row is one person's whole response.
 *
 * The table scrolls inside its own box. A ten-question survey is wider than the page,
 * and a document that scrolls sideways takes the rest of the results with it.
 */
export function RespondentTable({
  matrix,
  runs,
  openRun,
  onOpen,
}: {
  matrix: AnswersMatrix;
  /** The sliced runs, so the grid shows the group the rest of the page is describing. */
  runs: MatrixRun[];
  openRun: string | null;
  onOpen: (runId: string) => void;
}) {
  const msg = useT();
  const questions = [...matrix.questions].sort((a, b) => a.position - b.position);

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="text-md font-semibold">{msg.results.respondents}</h2>
        <Button
          variant="secondary"
          size="sm"
          onClick={() =>
            downloadCsv(
              // The slice is in the file as well as on the page, so a download taken
              // while filtered is not mistaken later for the whole survey.
              `${matrix.title.replace(/[^\w -]/g, "")}${
                runs.length === matrix.runs.length ? "" : "-filtered"
              }.csv`,
              matrixToCsv(matrix, runs, msg),
            )
          }
        >
          <Download aria-hidden />
          {msg.results.exportCsv}
        </Button>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>{msg.results.tableRespondent}</TableHead>
            <TableHead>{msg.results.tableStatus}</TableHead>
            {questions.map((question, i) => (
              <TableHead key={question.id} title={question.text}>
                <span className="block max-w-40 truncate font-normal normal-case">
                  {msg.builder.questionLabel(i + 1)}: {question.text}
                </span>
              </TableHead>
            ))}
          </TableRow>
        </TableHeader>
        <TableBody>
          {runs.map((run) => {
            const scripted = new Map(
              run.answers.filter((a) => a.kind === "scripted").map((a) => [a.question_id, a.value]),
            );
            return (
              <TableRow
                key={run.run_id}
                className={run.run_id === openRun ? "bg-surface" : undefined}
              >
                <TableCell>
                  <Button variant="link" size="sm" onClick={() => onOpen(run.run_id)}>
                    {run.respondent_label}
                  </Button>
                </TableCell>
                <TableCell>
                  <Badge variant={run.status === "completed" ? "neutral" : "warn"}>
                    {run.status === "completed"
                      ? msg.results.statusComplete
                      : msg.results.statusInProgress}
                  </Badge>
                </TableCell>
                {questions.map((question) => {
                  const value = scripted.get(question.id);
                  return (
                    <TableCell key={question.id} className="max-w-56 text-sm">
                      {value ? (
                        readAnswer(value, msg)
                      ) : (
                        <span className="text-muted">{msg.results.notAnswered}</span>
                      )}
                    </TableCell>
                  );
                })}
              </TableRow>
            );
          })}
        </TableBody>
      </Table>
    </div>
  );
}
