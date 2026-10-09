import { useEffect, useState } from "react";
import { useNavigate } from "react-router";
import { usePuterStore } from "~/lib/puter";

const WipeApp = () => {
    const { auth, isLoading, error, clearError, fs, ai, kv } = usePuterStore();
    const navigate = useNavigate();
    const [files, setFiles] = useState<FSItem[]>([]);

    const loadFiles = async () => {
        const files = (await fs.readDir("./")) as FSItem[];
        setFiles(files);
    };

    useEffect(() => {
        loadFiles();
    }, []);

    useEffect(() => {
        if (!isLoading && !auth.isAuthenticated) {
            navigate("/auth?next=/wipe");
        }
    }, [isLoading]);

    const handleDelete = async () => {
        await Promise.all(files.map((file) => fs.delete(file.path)));
        await kv.flush();
        loadFiles();
    };

    if (isLoading) {
        return <main className="container-page py-10 text-sm text-muted">Loading…</main>;
    }

    if (error) {
        return <main className="container-page py-10 text-sm text-fail">Error: {error}</main>;
    }

    return (
        <main className="container-page flex flex-col gap-6 py-10">
            <div>
                <h1 className="text-2xl font-semibold tracking-tight">Wipe app data</h1>
                <p className="mt-1 text-sm text-muted">Signed in as {auth.user?.username}. Deletes every file and review Scanly has stored.</p>
            </div>
            <ul className="panel divide-y divide-line text-sm">
                {files.length === 0 && <li className="px-4 py-3 text-subtle">No files stored.</li>}
                {files.map((file) => (
                    <li key={file.id} className="px-4 py-3 num">{file.name}</li>
                ))}
            </ul>
            <div>
                <button className="btn-danger" onClick={() => handleDelete()}>
                    Wipe app data
                </button>
            </div>
        </main>
    );
};

export default WipeApp;