import { useEffect, useState } from "react";
import { Link } from "react-router";
import DeleteResumeButton from "~/components/DeleteResumeButton";
import { usePuterStore } from "~/lib/puter";
import { cn, scoreTone, toneText, verdict } from "~/lib/utils";

const dateFormat = new Intl.DateTimeFormat(undefined, { month: "short", day: "numeric", year: "numeric" });

// One row in the review history.
const ResumeCard = ({ resume, onDeleted }: { resume: Resume; onDeleted: () => void }) => {
    const { fs } = usePuterStore();
    const [imageUrl, setImageUrl] = useState("");
    const { id, companyName, jobTitle, feedback, imagePath, createdAt } = resume;
    const score = feedback.overallScore;

    useEffect(() => {
        let url = "";
        fs.read(imagePath).then((blob) => {
            if (!blob) return;
            url = URL.createObjectURL(blob);
            setImageUrl(url);
        });
        return () => { if (url) URL.revokeObjectURL(url); };
    }, [imagePath]);

    return (
        <li className="group relative flex items-center gap-4 px-4 py-3 transition-colors hover:bg-hover">
            <div className="h-[72px] w-14 shrink-0 overflow-hidden rounded border border-line bg-bg">
                {imageUrl && <img src={imageUrl} alt="" className="size-full object-cover object-top" />}
            </div>

            <div className="min-w-0 flex-1">
                <Link to={`/resume/${id}`} className="block truncate font-medium after:absolute after:inset-0 after:content-[''] focus-visible:outline-none focus-visible:after:outline-2 focus-visible:after:-outline-offset-2 focus-visible:after:outline-accent">
                    {companyName || "Untitled review"}
                </Link>
                <p className="truncate text-sm text-muted">{jobTitle || "No job title"}</p>
            </div>

            <div className="hidden w-56 text-sm text-muted md:block">{verdict(score)}</div>
            <div className="hidden w-28 text-sm text-subtle tabular-nums sm:block">
                {createdAt ? dateFormat.format(createdAt) : "—"}
            </div>
            <div className={cn("w-14 text-right text-lg font-medium num", toneText[scoreTone(score)])}>
                {score}
            </div>

            {/* sits above the row link's overlay */}
            <div className="relative z-[1]">
                <DeleteResumeButton resume={resume} onDeleted={onDeleted} />
            </div>
        </li>
    );
};

export default ResumeCard;
