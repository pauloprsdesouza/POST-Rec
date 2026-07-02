import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";
import { useTranslation } from "react-i18next";

function normalizeTopic(value: string): string {
  return value.trim();
}

function isDuplicateTopic(topics: string[], candidate: string): boolean {
  const normalized = candidate.toLowerCase();
  return topics.some((topic) => topic.toLowerCase() === normalized);
}

export interface SeedTopicsInputHandle {
  flushDraft: () => string[];
}

interface SeedTopicsInputProps {
  value: string[];
  onChange: (topics: string[]) => void;
  id?: string;
  placeholder?: string;
  disabled?: boolean;
}

export const SeedTopicsInput = forwardRef<SeedTopicsInputHandle, SeedTopicsInputProps>(
  function SeedTopicsInput({ value, onChange, id, placeholder, disabled = false }, ref) {
    const { t } = useTranslation();
    const inputRef = useRef<HTMLInputElement>(null);
    const [draft, setDraft] = useState("");
    const valueKey = value.join("\0");

    useEffect(() => {
      setDraft("");
    }, [valueKey]);

    const commitDraft = (topics: string[], nextDraft: string): string[] => {
      const topic = normalizeTopic(nextDraft);
      if (!topic || isDuplicateTopic(topics, topic)) {
        return topics;
      }
      return [...topics, topic];
    };

    const flushDraft = (): string[] => {
      const nextTopics = commitDraft(value, draft);
      if (nextTopics.length !== value.length) {
        onChange(nextTopics);
      }
      setDraft("");
      return nextTopics;
    };

    useImperativeHandle(ref, () => ({ flushDraft }), [value, draft, onChange]);

    const addTopics = (rawTopics: string[]) => {
      let nextTopics = [...value];
      for (const rawTopic of rawTopics) {
        const topic = normalizeTopic(rawTopic);
        if (!topic || isDuplicateTopic(nextTopics, topic)) {
          continue;
        }
        nextTopics = [...nextTopics, topic];
      }
      if (nextTopics.length !== value.length) {
        onChange(nextTopics);
      }
    };

    const removeTopic = (index: number) => {
      onChange(value.filter((_, topicIndex) => topicIndex !== index));
    };

    const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
      if (event.key === "Enter") {
        event.preventDefault();
        const nextTopics = commitDraft(value, draft);
        if (nextTopics.length !== value.length) {
          onChange(nextTopics);
        }
        setDraft("");
        return;
      }

      if (event.key === "Backspace" && draft === "" && value.length > 0) {
        event.preventDefault();
        removeTopic(value.length - 1);
      }
    };

    const handlePaste = (text: string) => {
      const parts = text.split(/\r?\n|,/).map(normalizeTopic).filter(Boolean);
      if (parts.length === 0) {
        return;
      }
      if (parts.length === 1) {
        return;
      }
      addTopics(parts);
      setDraft("");
    };

    return (
      <div
        className={`seed-topics-input${disabled ? " seed-topics-input--disabled" : ""}`}
        onClick={() => {
          if (!disabled) {
            inputRef.current?.focus();
          }
        }}
      >
        {value.map((topic, index) => (
          <span key={`${topic}-${index}`} className="seed-topics-input__chip">
            <span className="seed-topics-input__chip-label">{topic}</span>
            <button
              type="button"
              className="seed-topics-input__chip-remove"
              onClick={(event) => {
                event.stopPropagation();
                removeTopic(index);
              }}
              disabled={disabled}
              aria-label={t("preferences.seedTopicsRemove", { topic })}
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={inputRef}
          id={id}
          type="text"
          className="seed-topics-input__field"
          value={draft}
          disabled={disabled}
          placeholder={value.length === 0 ? placeholder : undefined}
          spellCheck
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={() => flushDraft()}
          onPaste={(event) => {
            const text = event.clipboardData.getData("text");
            if (/\r?\n|,/.test(text)) {
              event.preventDefault();
              handlePaste(text);
            }
          }}
        />
      </div>
    );
  },
);
