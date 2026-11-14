import { useEffect, useState } from 'react';
import { api, type Slot } from './api';
import { registerProviders } from './format';

export function useSlotIndex() {
  const [index, setIndex] = useState<Record<string, Slot>>({});
  useEffect(() => {
    api
      .listSlots()
      .then((slots) => {
        registerProviders(slots.map((s) => s.provider));
        setIndex(Object.fromEntries(slots.map((s) => [s.id, s])));
      })
      .catch(() => {});
  }, []);
  return index;
}
