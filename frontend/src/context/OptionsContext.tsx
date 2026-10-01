import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { profileApi } from "@/services/endpoints";
import type { Options } from "@/types/api";

// Persona/category options come from the backend so UI selectors and API
// validation always agree.
const OptionsContext = createContext<{ options: Options | null; error: boolean }>({ options: null, error: false });

export function OptionsProvider({ children }: { children: ReactNode }) {
  const [options, setOptions] = useState<Options | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    let alive = true;
    profileApi
      .options()
      .then((o) => alive && setOptions(o))
      .catch(() => alive && setError(true));
    return () => {
      alive = false;
    };
  }, []);

  return <OptionsContext.Provider value={{ options, error }}>{children}</OptionsContext.Provider>;
}

export const useOptions = () => useContext(OptionsContext);
