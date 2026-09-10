import { anfrage } from "./anfrage";
import type { BlockKurz, BlockVoll, LueckeEintrag, RegelKurz, RegelVoll } from "../types/wissen";

export function fetchRegeln(klasse = "", stufe = ""): Promise<RegelKurz[]> {
  const p = new URLSearchParams();
  if (klasse) p.set("klasse", klasse);
  if (stufe) p.set("stufe", stufe);
  return anfrage(`/wissen/regeln?${p}`);
}

export const fetchRegel = (id: string): Promise<RegelVoll> =>
  anfrage(`/wissen/regeln/${id}`);

export const fetchWissenKlassen = (): Promise<string[]> => anfrage("/wissen/klassen");

export const fetchBloecke = (): Promise<BlockKurz[]> => anfrage("/wissen/bloecke");

export const fetchBlock = (id: string): Promise<BlockVoll> =>
  anfrage(`/wissen/bloecke/${id}`);

export const fetchLuecken = (): Promise<LueckeEintrag[]> => anfrage("/wissen/luecken");
