// Single registry for every visual used across the site. All visuals are
// original local SVG components (no external image URLs to break or license).
// To swap in photography later, change the entries here — pages only reference keys.
import {
  Chalkboard,
  ClassroomScene,
  DeskLamp,
  FountainPen,
  KnowledgeNetwork,
  MentorPortrait,
  Notebook,
  OpenBook,
  Pencil,
  Signature,
} from "@/components/illustrations/Illustrations";

export const visuals = {
  fountainPen: FountainPen,
  pencil: Pencil,
  notebook: Notebook,
  openBook: OpenBook,
  chalkboard: Chalkboard,
  mentor: MentorPortrait,
  lamp: DeskLamp,
  knowledgeNetwork: KnowledgeNetwork,
  classroom: ClassroomScene,
  signature: Signature,
} as const;

export type VisualKey = keyof typeof visuals;
