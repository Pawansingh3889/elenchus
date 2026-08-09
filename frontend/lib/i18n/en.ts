/**
 * English, and the source of truth for every other locale.
 *
 * `Messages` is derived from this object, so every translation is checked against it
 * at compile time: a missing key is a type error rather than a blank label discovered
 * by a reader who cannot read the fallback either.
 *
 * Nested by area rather than flat, because a flat file of eighty keys is a file nobody
 * can find anything in. Functions rather than "{count} of {total}" placeholders, since
 * a function is type-checked and a placeholder string is not.
 */
export const en = {
  common: {
    loading: "Loading…",
    save: "Save",
    saving: "Saving…",
    publish: "Publish",
    publishing: "Publishing…",
    delete: "Delete",
    confirmDelete: "Confirm delete",
    cancel: "Cancel",
    dismiss: "dismiss",
    notFound: "Not found",
    deleting: "Deleting…",
  },
  topbar: {
    brandLead: "Survey",
    brandTail: "Service",
    build: "Build",
    respond: "Respond",
    actingAs: "Acting as",
    selectUser: "Select a user…",
    language: "Language",
  },
  home: {
    started: "started",
    completedLabel: "completed",
    inProgress: "in progress",
    closeSurvey: "Close survey",
    closing: "Closing…",
    noResponses: "No responses yet",
    title: "Survey templates",
    pickUser: "Pick a user in the top bar to start authoring.",
    goingToRespond: "Taking you to Respond…",
    empty: "No templates yet. Create one or draft with AI.",
    draftWithAi: "✦ Draft with AI",
    describePlaceholder:
      "Describe the survey… e.g. An onboarding survey for factory staff: their role, the systems they use daily, and their biggest data frustrations.",
  },
  builder: {
    pickUser: "Pick a user in the top bar.",
    titlePlaceholder: "Survey title",
    descriptionPlaceholder: "Description (optional)",
    questionPlaceholder: "Question text",
    responses: "Responses",
    addQuestion: "+ Add question",
    addOption: "+ Add option",
    optionPlaceholder: (n: number) => `Option ${n}`,
    required: "Required",
    allowFollowUps: "Allow follow-ups",
    allowOther: "Allow “other”",
    show: "Show",
    always: "always",
    onlyIf: "only if…",
    is: "is",
    isNot: "is not",
    answerPlaceholder: "answer",
    moveUp: "Move up",
    moveDown: "Move down",
    removeQuestion: "Delete question",
    removeOption: "Remove option",
    answerTypesTitle: "Answer types",
    answerTypesHint:
      "Tick the types this survey may use. Nothing ticked allows any type. The AI keeps to this on every refine.",
    typeNotAllowed: (typeLabel: string) => `this survey does not allow ${typeLabel}`,
    refineTitle: "✦ Refine with AI",
    refinePlaceholder: "Describe a change…",
    refine: "Refine",
    livePreview: "Live preview",
    previewEmpty: "Add a question to see the preview.",
    conversational: "Conversational",
    form: "Form",
    conditionNeedsValue:
      "Type the answer this question depends on, or set it back to “always”. The survey cannot be saved while the condition has no answer to match.",
    conditionsCleared: (n: number) =>
      n === 1
        ? "A visibility condition was cleared: the question it pointed at was removed or is no longer earlier."
        : `${n} visibility conditions were cleared: the question they pointed at was removed or is no longer earlier.`,
    typeChangeWarning: (typeLabel: string, count: number) =>
      `Changing this question to ${typeLabel} removes its ${count} ${count === 1 ? "option" : "options"}.\n\n` +
      "They will be restored if you change it back before saving.",
    questionLabel: (n: number) => `Question ${n}`,
    conditionHasNoAnswer: "its condition has no answer",
    selectHasNoOptions: "it has no options",
    publishBlocker: (n: number, problem: string) => `Question ${n}: ${problem}`,
  },
  respond: {
    title: "Open surveys",
    pickUser: "Pick a user in the top bar to take a survey.",
    goingToBuild: "Taking you to Build…",
    empty: "Nothing published yet. Publish a template to open it here.",
    start: "Start",
    continue: "Continue",
  },
  run: {
    pickUser: "Pick a user in the top bar to continue this survey.",
    answerPlaceholder: "Type your answer…",
    send: "Send",
    finishLater: "Finish later",
    finishLaterHint: "Your answers so far are saved; pick up where you left off.",
    editPrevious: "Edit my previous answer",
    editPreviousHint: "The question comes back so you can answer it again.",
    editPreviousConfirm:
      "Take back your previous answer? Anything the survey asked about it will be removed too, and you will answer that question again.",
    done: "Thanks. Your answers are saved.",
    orSayIt: "or say it in your own words below",
    other: "other…",
    yes: "Yes",
    no: "No",
    progress: (done: number, total: number) => `${done} of ${total}`,
  },
  results: {
    title: "Responses",
    pickAuthor: "Pick an author in the top bar to see responses.",
    empty: "No responses yet. Publish the survey and answer it to see it here.",
    pickOne: "Pick a response to read it.",
    nothingAnswered: "Nothing answered yet.",
    notAnswered: "Not answered",
    answers: "Answers",
    transcript: "Transcript",
    summary: "Summary",
    followUp: "follow-up",
    exportCsv: "CSV",
    exportJson: "JSON",
    exportCsvHint: "Every answer as a spreadsheet row, opens directly in Excel",
    exportJsonHint: "Every answer as structured JSON",
    probeHint:
      "Follow-ups the engine allowed on this question. A probe is counted when it is asked, so this can exceed the number of follow-up answers below.",
  },
};

/** The shape every locale must satisfy.
 *
 *  Deliberately not `as const`: that would freeze each value to its English literal
 *  type, so `save: "Guardar"` would fail as "not assignable to type 'Save'". What is
 *  wanted here is the shape, meaning the keys, and `string` where a string belongs. */
export type Messages = typeof en;
