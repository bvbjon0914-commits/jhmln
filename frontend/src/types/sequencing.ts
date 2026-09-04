/**
 * Weiche Reihenfolge-Hinweise zwischen Auskunftsarten. Mehrere Register sind
 * flurstücksbezogen indiziert - ohne die Flurstücksnummer aus Grundbuch/
 * Kataster riskiert man bei Grundstücken mit mehreren/zusammengelegten
 * Flurstücken eine falsche oder unvollständige Auskunft. Das ist bewusst nur
 * ein Hinweis, kein Zwangs-Gate: manche Behörden verlangen kein Flurstück,
 * und die Nummer könnte schon aus einem früheren Vorgang bekannt sein.
 */

export const TIER0_TYPE_IDS = ["GRUNDBUCH", "KATASTER"];

export const SEQUENCING_HINTS: Record<string, string> = {
  ALTLASTEN:
    "Das Altlastenkataster ist meist flurstücksbezogen geführt – Grundbuch- oder Katasterauskunft liefert die Flurstücksnummer.",
  BAULASTEN:
    "Das Baulastenverzeichnis ist in den meisten Bundesländern flurstücksbezogen geführt – Grundbuch- oder Katasterauskunft liefert die Flurstücksnummer.",
  ERSCHLIESSUNG:
    "Die Beitragsveranlagung ist an ein konkretes Flurstück gebunden – Grundbuch- oder Katasterauskunft liefert die Flurstücksnummer.",
  BODENDENKMALSCHUTZ:
    "Bodendenkmäler werden häufig parzellenscharf erfasst – Grundbuch- oder Katasterauskunft liefert die Flurstücksnummer.",
};

/**
 * Liefert für jede ausgewählte Stufe-1-Auskunftsart einen Hinweistext, sofern
 * weder in der aktuellen Auswahl noch unter den bereits erledigten Typen
 * (satisfiedIds) eine Stufe-0-Auskunftsart (Grundbuch/Kataster) enthalten ist.
 */
export function computeSequencingHints(
  selectedIds: string[],
  satisfiedIds: string[] = []
): Record<string, string> {
  const hasTier0 = [...selectedIds, ...satisfiedIds].some((id) => TIER0_TYPE_IDS.includes(id));
  if (hasTier0) return {};

  const hints: Record<string, string> = {};
  for (const id of selectedIds) {
    if (SEQUENCING_HINTS[id]) {
      hints[id] = SEQUENCING_HINTS[id];
    }
  }
  return hints;
}
