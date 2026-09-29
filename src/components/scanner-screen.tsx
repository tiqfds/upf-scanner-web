"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";

const INSTRUCTIONS_SEEN = "upf-instructions-seen";
const SIGNUP_DRAFT = "upf-signup-draft";

type Step = "permission" | "signup" | "instructions" | "camera";

type Signup = {
  firstName: string;
  lastName: string;
  email: string;
};

const emptySignup: Signup = { firstName: "", lastName: "", email: "" };

function readSignup(): Signup | null {
  const raw = sessionStorage.getItem(SIGNUP_DRAFT);
  if (!raw) {
    return null;
  }
  try {
    const parsed = JSON.parse(raw) as Signup;
    if (parsed.firstName && parsed.lastName && parsed.email) {
      return parsed;
    }
  } catch {
    return null;
  }
  return null;
}

export function ScannerScreen() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [step, setStep] = useState<Step>("permission");
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [signup, setSignup] = useState<Signup>(emptySignup);
  const [authNote, setAuthNote] = useState<string | null>(null);

  useEffect(() => {
    let stream: MediaStream | null = null;
    let cancelled = false;

    async function openCamera() {
      if (!navigator.mediaDevices?.getUserMedia) {
        setCameraError("This browser cannot open the camera.");
        return;
      }
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });
        if (cancelled) {
          stream.getTracks().forEach((track) => track.stop());
          return;
        }
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        const seen = localStorage.getItem(INSTRUCTIONS_SEEN) === "1";
        const signed = readSignup();
        if (!signed) {
          setStep("signup");
        } else if (!seen) {
          setStep("instructions");
        } else {
          setStep("camera");
        }
      } catch {
        setCameraError("Allow the camera to point at an ingredient list.");
      }
    }

    void openCamera();
    return () => {
      cancelled = true;
      stream?.getTracks().forEach((track) => track.stop());
    };
  }, []);

  function continueSignup(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const firstName = signup.firstName.trim();
    const lastName = signup.lastName.trim();
    const email = signup.email.trim();
    if (!firstName || !lastName || !email.includes("@")) {
      setAuthNote("Enter a first name, last name, and email.");
      return;
    }
    sessionStorage.setItem(
      SIGNUP_DRAFT,
      JSON.stringify({ firstName, lastName, email }),
    );
    setAuthNote(null);
    setStep(localStorage.getItem(INSTRUCTIONS_SEEN) === "1" ? "camera" : "instructions");
  }

  function finishInstructions() {
    localStorage.setItem(INSTRUCTIONS_SEEN, "1");
    setStep("camera");
  }

  return (
    <main className="relative h-dvh w-full overflow-hidden bg-black text-white">
      <video
        ref={videoRef}
        className="h-full w-full object-cover"
        autoPlay
        muted
        playsInline
      />

      <button
        type="button"
        className="absolute top-4 right-4 flex h-10 w-10 items-center justify-center rounded-full bg-black/60 text-lg"
        aria-label="Show instructions"
        onClick={() => setStep("instructions")}
      >
        ?
      </button>

      {cameraError ? (
        <div className="absolute inset-0 flex items-end justify-center p-6">
          <p className="max-w-sm rounded-2xl bg-black/80 px-4 py-3 text-center text-sm">
            {cameraError}
          </p>
        </div>
      ) : null}

      {step === "signup" ? (
        <div className="absolute inset-0 flex items-end justify-center bg-black/40 p-4 sm:items-center">
          <form
            className="w-full max-w-sm rounded-3xl bg-white p-5 text-zinc-950"
            onSubmit={continueSignup}
          >
            <h1 className="text-lg font-semibold">Create your account</h1>
            <p className="mt-1 text-sm text-zinc-600">
              First name, last name, and email. Then you can scan.
            </p>
            <div className="mt-4 grid gap-2">
              <ProviderButton
                label="Continue with Apple"
                onClick={() =>
                  setAuthNote("Apple sign-in connects after the Supabase project is chosen.")
                }
              />
              <ProviderButton
                label="Continue with Google"
                onClick={() =>
                  setAuthNote("Google sign-in connects after the Supabase project is chosen.")
                }
              />
            </div>
            <label className="mt-4 block text-sm">
              First name
              <input
                className="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2"
                autoComplete="given-name"
                value={signup.firstName}
                onChange={(event) =>
                  setSignup({ ...signup, firstName: event.target.value })
                }
              />
            </label>
            <label className="mt-3 block text-sm">
              Last name
              <input
                className="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2"
                autoComplete="family-name"
                value={signup.lastName}
                onChange={(event) =>
                  setSignup({ ...signup, lastName: event.target.value })
                }
              />
            </label>
            <label className="mt-3 block text-sm">
              Email
              <input
                className="mt-1 w-full rounded-xl border border-zinc-300 px-3 py-2"
                type="email"
                autoComplete="email"
                value={signup.email}
                onChange={(event) =>
                  setSignup({ ...signup, email: event.target.value })
                }
              />
            </label>
            {authNote ? <p className="mt-3 text-sm text-zinc-600">{authNote}</p> : null}
            <button
              type="submit"
              className="mt-4 w-full rounded-full bg-zinc-950 py-3 text-sm font-medium text-white"
            >
              Continue
            </button>
          </form>
        </div>
      ) : null}

      {step === "instructions" ? (
        <div className="absolute inset-0 flex items-end justify-center p-4 sm:items-center">
          <section className="w-full max-w-sm rounded-3xl bg-white p-5 text-zinc-950">
            <ol className="space-y-3 text-sm">
              <li className="flex items-center gap-3">
                <ListIcon />
                Point at the ingredient list
              </li>
              <li className="flex items-center gap-3">
                <HoldIcon />
                Tap Scan when the list is in the frame
              </li>
            </ol>
            <p className="mt-4 text-sm leading-5 text-zinc-950">
              NOVA sorts foods into four groups by how they&apos;re processed. Group 4 means
              ultra-processed: the product contains at least one ingredient rarely used in home
              cooking or an additive used for taste, color, or texture. In large studies, eating
              more ultra-processed food is associated with higher risk of type 2 diabetes, obesity,
              heart attack, stroke, and depression. A NOVA group tells you how a food is processed,
              not how healthy it is.
            </p>
            <p className="mt-3 text-sm font-semibold">Sources</p>
            <ul className="mt-1 space-y-2 text-sm">
              <li>
                <a className="text-blue-700 underline" href="https://doi.org/10.1017/S1368980018003762">
                  Ultra-processed foods: what they are and how to identify them
                </a>
              </li>
              <li>
                <a
                  className="text-blue-700 underline"
                  href="https://www.heart.org/-/media/Files/About-Us/Policy-Research/Fact-Sheets/Access-to-Healthy-Food/Ultraprocessed-Foods-Fact-Sheet-2026.pdf"
                >
                  Regulating Ultraprocessed Foods
                </a>
              </li>
              <li>
                <a className="text-blue-700 underline" href="https://doi.org/10.1016/j.advnut.2023.09.009">
                  Ultra-Processed Foods and Human Health: A Systematic Review and Meta-Analysis of
                  Prospective Cohort Studies
                </a>
              </li>
              <li>
                <a className="text-blue-700 underline" href="https://www.fao.org/3/ca5644en/ca5644en.pdf">
                  Ultra-processed foods, diet quality, and health using the NOVA classification system
                </a>
              </li>
            </ul>
            <button
              type="button"
              className="mt-5 w-full rounded-full bg-zinc-950 py-3 text-sm font-medium text-white"
              onClick={finishInstructions}
            >
              Got it
            </button>
          </section>
        </div>
      ) : null}
    </main>
  );
}

function ProviderButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="w-full rounded-full border border-zinc-300 py-2.5 text-sm"
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function ListIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <rect x="3" y="3" width="14" height="14" rx="2" fill="none" stroke="currentColor" />
      <path d="M6 8h8M6 12h5" stroke="currentColor" />
    </svg>
  );
}

function HoldIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" aria-hidden="true">
      <circle cx="10" cy="10" r="6" fill="none" stroke="currentColor" />
      <circle cx="10" cy="10" r="2" fill="currentColor" />
    </svg>
  );
}
