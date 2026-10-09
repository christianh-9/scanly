import { useState } from 'react'
import { useDropzone, type FileRejection } from 'react-dropzone'
import { cn, formatSize } from '~/lib/utils'
import { FileIcon, UploadIcon, XIcon } from './Icons'

interface FileUploaderProps {
    onFileSelect?: (file: File | null) => void
    disabled?: boolean
}

const maxFileSize = 20 * 1024 * 1024

const FileUploader = ({ onFileSelect, disabled }: FileUploaderProps) => {
    const [selectedFile, setSelectedFile] = useState<File | null>(null)
    const [rejection, setRejection] = useState('')

    const select = (file: File | null) => {
        setSelectedFile(file)
        onFileSelect?.(file)
    }

    const onDropRejected = ([rejected]: FileRejection[]) => {
        const code = rejected?.errors[0]?.code
        setRejection(code === 'file-too-large'
            ? `That file is ${formatSize(rejected.file.size)}. The limit is ${formatSize(maxFileSize)}.`
            : 'Only PDF files are supported. Export your resume as a PDF and try again.')
    }

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop: ([file]) => { setRejection(''); select(file ?? null) },
        onDropRejected,
        multiple: false,
        accept: { 'application/pdf': ['.pdf'] },
        maxSize: maxFileSize,
        disabled,
    })

    if (selectedFile) {
        return (
            <div className="flex items-center gap-3 rounded-md border border-line bg-raised px-3 py-3">
                <div className="flex size-9 shrink-0 items-center justify-center rounded border border-line text-muted">
                    <FileIcon />
                </div>
                <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{selectedFile.name}</p>
                    <p className="text-xs text-subtle num">{formatSize(selectedFile.size)}</p>
                </div>
                <button type="button" className="btn-icon" onClick={() => select(null)} disabled={disabled} aria-label="Remove file">
                    <XIcon />
                </button>
            </div>
        )
    }

    return (
        <div>
            <div
                {...getRootProps()}
                className={cn(
                    'flex cursor-pointer flex-col items-center gap-3 rounded-md border border-dashed px-6 py-10 text-center transition-colors',
                    isDragActive ? 'border-accent bg-accent/5' : 'border-line-strong hover:border-subtle hover:bg-hover/50',
                )}
            >
                <input {...getInputProps()} id="resume-file" />
                <div className="flex size-10 items-center justify-center rounded-full border border-line text-muted">
                    <UploadIcon />
                </div>
                <div>
                    <p className="text-sm">
                        <span className="font-medium text-fg">{isDragActive ? 'Drop to upload' : 'Click to upload'}</span>
                        {!isDragActive && <span className="text-muted"> or drag and drop</span>}
                    </p>
                    <p className="mt-1 text-xs text-subtle">PDF up to {formatSize(maxFileSize)}</p>
                </div>
            </div>
            {rejection && <p role="alert" className="mt-2 text-sm text-fail">{rejection}</p>}
        </div>
    )
}

export default FileUploader
