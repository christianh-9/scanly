import { useRef, useState } from "react";
import { deleteResume } from "~/lib/puter";
import { SpinnerIcon, TrashIcon } from "./Icons";

interface Props {
  resume: Resume;
  onDeleted: () => void;
  // "icon" for list rows, "button" for the review page header
  variant?: "icon" | "button";
}

const DeleteResumeButton = ({ resume, onDeleted, variant = "icon" }: Props) => {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState("");
  const name = [resume.companyName, resume.jobTitle].filter(Boolean).join(" · ") || "this resume";

  const open = (e: React.MouseEvent) => {
    // rows are links; don't navigate when deleting
    e.preventDefault();
    e.stopPropagation();
    setError("");
    dialogRef.current?.showModal();
  };

  const confirm = async () => {
    setDeleting(true);
    try {
      await deleteResume(resume);
      dialogRef.current?.close();
      onDeleted();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Couldn't delete this review. Try again.");
    } finally {
      setDeleting(false);
    }
  };

  return (
    <>
      {variant === "icon" ? (
        <button type="button" className="btn-icon" onClick={open} aria-label={`Delete review for ${name}`}>
          <TrashIcon />
        </button>
      ) : (
        <button type="button" className="btn-secondary" onClick={open}>
          <TrashIcon /> Delete
        </button>
      )}

      <dialog
        ref={dialogRef}
        onClick={(e) => e.stopPropagation()}
        onCancel={(e) => deleting && e.preventDefault()}
        className="m-auto w-[min(420px,calc(100vw-32px))] rounded-lg border border-line bg-raised p-0 text-fg shadow-[0_16px_48px_rgba(0,0,0,0.6)] backdrop:bg-black/70"
      >
        <div className="flex flex-col gap-2 p-5">
          <h2 className="text-base font-semibold">Delete review?</h2>
          <p className="text-sm text-muted">
            This permanently deletes the review for <span className="text-fg">{name}</span>, along with the uploaded PDF and its preview. It can't be undone.
          </p>
          {error && <p role="alert" className="text-sm text-fail">{error}</p>}
        </div>
        <div className="flex justify-end gap-2 border-t border-line bg-bg/40 px-5 py-3">
          <button type="button" className="btn-secondary" onClick={() => dialogRef.current?.close()} disabled={deleting} autoFocus>
            Cancel
          </button>
          <button type="button" className="btn-danger" onClick={confirm} disabled={deleting}>
            {deleting && <SpinnerIcon />} {deleting ? "Deleting…" : "Delete review"}
          </button>
        </div>
      </dialog>
    </>
  );
};

export default DeleteResumeButton;
