"use client";

import { ANSWER_TYPES } from "@/lib/answerTypes";
import { PRESET_TYPES, presetFor, type PresetKey } from "@/lib/answerTypePresets";
import { useT } from "@/lib/i18n/useT";
import type { AnswerType } from "@/lib/types";

interface Props {
  allowedTypes: AnswerType[];
  onChange: (types: AnswerType[]) => void;
  /** Rendered above the control. The builder and the draft box introduce it differently:
   *  one is editing a survey's policy, the other is stating it before anything exists. */
  hint: string;
}

/**
 * Which answer types a survey may use, asked the way an author states it.
 *
 * One choice, not eight. The eight checkboxes are still there behind Advanced, because
 * a set that is nobody's preset is a real thing to want, and because the preset list
 * should not become the limit of what can be expressed. Choosing a preset replaces the
 * set; ticking a box afterwards moves the choice to Custom, which the summary then says.
 *
 * Shared by the builder's settings panel and the Draft-with-AI box, so the two cannot
 * drift into offering different vocabularies for the same stored field.
 */
export function AnswerTypePolicy({ allowedTypes, onChange, hint }: Props) {
  const msg = useT();
  const preset = presetFor(allowedTypes);

  const presets: { key: PresetKey; label: string }[] = [
    { key: "any", label: msg.builder.presetAny },
    { key: "no_free_text", label: msg.builder.presetNoFreeText },
    { key: "closed_only", label: msg.builder.presetClosedOnly },
  ];

  const toggle = (type: AnswerType, allowed: boolean) => {
    // Ticking a box on "any" starts from every type rather than from nothing: the author
    // is narrowing a survey that allows everything, and starting from the empty set would
    // read as banning the seven types they did not touch.
    const from = allowedTypes.length ? allowedTypes : ANSWER_TYPES.map((t) => t.value);
    onChange(allowed ? [...from, type] : from.filter((v) => v !== type));
  };

  return (
    <div className="policy">
      <p className="muted types-hint">{hint}</p>
      <div className="policy-presets">
        {presets.map((p) => (
          <label key={p.key} className={preset === p.key ? "chip chip-on" : "chip"}>
            <input
              type="radio"
              name="answer-type-preset"
              checked={preset === p.key}
              onChange={() => onChange(PRESET_TYPES[p.key as Exclude<PresetKey, "custom">])}
            />
            {p.label}
          </label>
        ))}
        {preset === "custom" ? <span className="chip chip-on">{msg.builder.presetCustom}</span> : null}
      </div>

      <details className="policy-advanced">
        <summary className="muted">{msg.builder.presetAdvanced}</summary>
        <div className="types-grid">
          {ANSWER_TYPES.map((t) => (
            <label key={t.value}>
              <input
                type="checkbox"
                // On "any" every type is genuinely permitted, so every box reads ticked.
                checked={!allowedTypes.length || allowedTypes.includes(t.value)}
                onChange={(e) => toggle(t.value, e.target.checked)}
              />
              {t.label}
            </label>
          ))}
        </div>
      </details>
    </div>
  );
}
