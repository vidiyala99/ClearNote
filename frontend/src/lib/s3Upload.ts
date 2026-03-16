interface UploadArgs {
  upload_url: string;
  upload_fields: Record<string, string>;
  blob: Blob;
  onProgress?: (progress: number) => void;
}

export const s3Upload = ({ upload_url, upload_fields, blob, onProgress }: UploadArgs) => {
  let xhr: XMLHttpRequest;

  const promise = new Promise<void>((resolve, reject) => {
    xhr = new XMLHttpRequest();
    xhr.open("POST", upload_url, true);

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) {
        onProgress(Math.round((e.loaded / e.total) * 100));
      }
    };

    xhr.onload = () => {
      if (xhr.status === 204 || (xhr.status >= 200 && xhr.status < 300)) {
        resolve();
      } else {
        reject(new Error(`S3 upload failed with status ${xhr.status}`));
      }
    };

    xhr.onerror = () => reject(new Error("S3 upload failed due to network error"));
    xhr.onabort = () => reject(new Error("S3 upload aborted"));

    const formData = new FormData();
    
    // AWS S3 Presigned POST requires fields appended BEFORE the 'file' field
    Object.entries(upload_fields).forEach(([key, value]) => {
      formData.append(key, value);
    });
    
    formData.append("file", blob);

    xhr.send(formData);
  });

  return {
    promise,
    cancel: () => xhr && xhr.abort()
  };
}
