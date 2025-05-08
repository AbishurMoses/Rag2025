"use client";

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import Uppy, { UppyFile, Meta } from '@uppy/core'; // Import UppyFile and Meta types
import Tus from '@uppy/tus';
import Dashboard from '@uppy/dashboard';
import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';
import { FileList } from './FileList';
import { UploadIcon, TrashIcon } from 'lucide-react';
import { FileItem } from './mockData';



export default function FileManager() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);
  const [files, setFiles] = useState<FileItem[]>([]);
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [uploadedFileNames, setUploadedFileNames] = useState<string[]>([]); // State to track names sent to backend
  const [isUploading, setIsUploading] = useState(false); // Consider if this state is still needed
  const [isConverting, setIsConverting] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [sortMenuOpen, setSortMenuOpen] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(false);
  const [message, setMessage] = useState('');
  const [sortConfig, setSortConfig] = useState({
    field: 'name',
    direction: 'asc' as 'asc' | 'desc'
  });
  // Initialize Uppy instances
  const [uppy] = useState(() => new Uppy({
    restrictions: {
      allowedFileTypes: ["application/pdf"], // Restrict to PDF
      maxFileSize: 100 * 1024 * 1024, // Example: 100MB limit
    },
  }));
  const [uppyTxt] = useState(() => new Uppy()); // Keep if needed for TXT uploads

  // --- Supabase Client ---
  // It's often better to create the client once, but creating it inside functions
  // where needed is also fine for client components.
  // const supabase = createClient(); // Optional: Create once if used frequently outside useEffects

  // Check admin role
  useEffect(() => {
    const checkRole = async () => {
      const supabase = createClient(); // Create client instance here
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        setAuthorized(false);
        return;
      }
      const { data: profile, error } = await supabase
        .from("profiles")
        .select("role")
        .eq("user_id", user.id)
        .single();
      if (error || profile?.role !== "admin") {
        setAuthorized(false);
        return;
      }
      setAuthorized(true);
    };
    checkRole().finally(() => setLoading(false));
  }, []); // Dependency array is empty, runs once on mount

  // Fetch list of files from the 'ragfiles' bucket txt files 
  useEffect(() => {
    if (authorized === null) return; // dont run waiting 
    // Don't fetch if not authorized
    if (!authorized) {
      console.log("Not authorized skipping file fetch.");
      return;
    }

    const fetchFiles = async () => {
      const supabase = createClient(); // Create client instance here
      setMessage("Loading files..."); // Provide loading feedback
      const { data, error } = await supabase.storage.from("ragfiles").list(); // List from 'ragfiles'
      if (error) {
        console.error("Error fetching files from ragfiles:", error);
        setMessage(`Failed to load files: ${error.message}`);
        return;
      }

      // Map the fetched data to the FileItem structure
      const mapped = (data || [])
        // Filter out potential placeholder files if Supabase storage adds them
        .filter(f => f.name !== '.emptyFolderPlaceholder')
        .map((f): FileItem => ({ // Explicitly type the return of map
          id: f.id ?? f.name, // Use id if available, fallback to name
          name: f.name,
          size: f.metadata?.size ?? 0, // Use nullish coalescing
          lastModified: new Date(f.updated_at ?? f.created_at ?? Date.now()), // Prefer updated_at, fallback
          type: f.metadata?.mimetype ?? 'text/plain' // Default to text/plain for ragfiles
        }));
      setFiles(mapped);
      setMessage(mapped.length > 0 ? "" : "No files found."); // Clear message or show "No files"
    };
    fetchFiles();
  }, [authorized, refreshTrigger]); // Re-run if authorization status changes

  // Initialize Uppy for modal PDF upload to 'pdf' bucket
  useEffect(() => {
    // Ensure Uppy is only initialized once and when authorized
    if (!authorized || uppy.getPlugin('Tus')) return; // Prevent re-initialization

    const supabase = createClient(); // Create client instance here

    const initializeUppy = async () => {
      const { data: { session }, error: sessionError } = await supabase.auth.getSession();

      if (sessionError || !session) {
        console.error("Error getting Supabase session:", sessionError);
        setMessage("Could not authenticate for upload. Please refresh.");
        return; // Stop initialization if no session
      }

      uppy.use(Tus, {
        endpoint: `${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/upload/resumable`,
        retryDelays: [0, 3000, 5000, 10000, 20000],
        headers: {
          authorization: `Bearer ${session.access_token}`,
          apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "", // Ensure this is set in your env
        },
        uploadDataDuringCreation: true,
        removeFingerprintOnSuccess: true,
        chunkSize: 6 * 1024 * 1024, // 6MB chunks
        allowedMetaFields: ["bucketName", "objectName", "contentType", "cacheControl"],
        onError: (error) => {
          console.error("Uppy Tus Error:", error);
          setMessage(`Upload failed: ${error.message || 'Unknown error'}`);
        },
      })
        .on("file-added", async (file) => {
          // File type and existence checks before setting metadata
          const supabase = createClient(); // Instance for this async operation

          // 1. Check for .pdf file type strictly
          const isPdf = file.name?.toLowerCase().endsWith(".pdf") && file.type === "application/pdf";
          if (!isPdf) {
            uppy.info(`❌ "${file.name}" is not a valid PDF file. Upload cancelled.`, 'error', 5000);
            uppy.removeFile(file.id); // Remove the invalid file from Uppy's queue
            return;
          }

          // 2. Check if the file already exists in the 'pdf' bucket
          // Use list with search for exact match potential
          const { data: existingFiles, error: listError } = await supabase
            .storage
            .from("pdf") // Target 'pdf' bucket
            .list('', { search: file.name, limit: 1 }); // Search specifically for this file name

          if (listError) {
            console.error("Error checking for existing file in bucket:", listError);
            uppy.info(`⚠️ Could not verify if "${file.name}" exists. Upload cancelled.`, 'warning', 5000);
            uppy.removeFile(file.id);
            return;
          }

          const alreadyExists = existingFiles && existingFiles.length > 0 && existingFiles[0].name === file.name;

          if (alreadyExists) {
            uppy.info(`⚠️ "${file.name}" already exists in the bucket. Upload cancelled.`, 'warning', 5000);
            uppy.removeFile(file.id);
            return;
          }

          // 3. Set metadata for Supabase Storage (target 'pdf' bucket)
          // This metadata is used by the Tus plugin during upload
          file.meta = {
            ...file.meta,
            bucketName: "pdf", // Target bucket
            objectName: file.name, // Use original file name for the object path
            contentType: "application/pdf", // Set content type
            cacheControl: "3600" // Example cache control
          };
        })
        .on("upload-success", (file, response) => { // Uppy passes file and response
          // --- Start of the fix ---
          // 1. Check if file and file.name exist (Fix for TypeScript error)
          if (file && file.name) {
            setMessage(`Upload of ${file.name} successful ✅`);
            console.log('Upload successful for:', file.name, 'Response:', response);

            // 2. Calculate the new array immediately (Fix for async state)
            // This assumes you want to track *all* successfully uploaded PDF names
            // If you only want to send the *current* file, adjust accordingly.
            const newFileNames = [...uploadedFileNames, file.name];

            // 3. Update state (this is async)
            setUploadedFileNames(newFileNames);

            // 4. Define the URL for your backend endpoint
            // const apiUrl = 'http://127.0.0.1:5000/convertFiles'; // Your backend endpoint
            const apiUrl = 'http://10.10.129.80:5000/convertFiles'; // Your backend endpoint

            console.log('Sending file names for conversion:', newFileNames); // Log the array being sent

            // 5. Perform the POST request using the 'newFileNames' variable
            setIsConverting(true);
            setTimeout(() => setIsConverting(true), 10); // Small delay forces refresh
            fetch(apiUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                // Add any other headers your API might require
              },
              // Use the 'input' key and the 'newFileNames' variable directly
              body: JSON.stringify({ input: newFileNames }) // Send the updated list
            })
              .then(fetchResponse => { // Rename to avoid conflict with Uppy 'response'
                if (!fetchResponse.ok) {
                  // Try to get error details from the response body
                  return fetchResponse.text().then(text => {
                    throw new Error(`Backend error! Status: ${fetchResponse.status}, Message: ${text}`);
                  });
                }
                // Check content type before parsing JSON
                const contentType = fetchResponse.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                  // console.log(fetchResponse.json)
                  return fetchResponse.json();
                } else {
                  return fetchResponse.text(); // Handle non-JSON success response if needed
                }
              })
              .then(data => {
                console.log('Server conversion response:', data);
                setMessage(`Backend processed: ${JSON.stringify(data)}`); // Show backend response
                setRefreshTrigger(prev => !prev); // toggles between true and false
              })
              .catch(async error => {
                // ❌ Conversion failed, delete file from Supabase 'pdf' bucket
                const supabase = createClient();
                const { error: deleteError } = await supabase
                  .storage
                  .from("pdf")  // make sure 'pdf' is your actual bucket
                  .remove([file.name]);

                if (deleteError) {
                  console.error('Error deleting failed file:', deleteError.message);
                } else {
                  console.log(`Deleted ${file.name} from pdf bucket due to conversion failure`);
                }
                console.error('Fetch error during conversion:', error);
                setMessage(`Error sending files to backend: ${error.message}`);
              })
              .finally(() => {
                setIsConverting(false);
              });;

            // --- Refreshing the file list (from 'ragfiles') might be confusing here ---
            // This upload was to the 'pdf' bucket. The file list state (`files`)
            // currently shows files from the 'ragfiles' bucket.
            // Decide if you want to:
            // a) Also list files from the 'pdf' bucket.
            // b) Only list 'ragfiles' (TXT files) and don't refresh here.
            // c) Trigger a refresh based on the backend response indicating TXT creation.

            // Example: If you want to refresh the 'ragfiles' list (maybe backend creates TXT)
            /*
            const supabase = createClient();
            supabase.storage.from("ragfiles").list().then(({ data, error }) => {
              if (error) {
                  console.error("Error refreshing ragfiles list:", error);
                  return; // Don't update state on error
              }
              const mapped = (data || [])
                  .filter(f => f.name !== '.emptyFolderPlaceholder')
                  .map((f): FileItem => ({
                      id: f.id ?? f.name,
                      name: f.name,
                      size: f.metadata?.size ?? 0,
                      lastModified: new Date(f.updated_at ?? f.created_at ?? Date.now()),
                      type: f.metadata?.mimetype ?? 'text/plain'
                  }));
              setFiles(mapped); // Update the displayed file list
            });
            */

          } else {
            console.error("Upload success event triggered but file or file.name is undefined.");
            setMessage("An error occurred during upload post-processing.");
          }
          // --- End of the fix ---
        }); // End of .on("upload-success")

      // Initialize the Dashboard plugin
      uppy.use(Dashboard, {
        inline: false, // Open as a modal
        target: "body", // Attach modal to body
        trigger: null, // Don't automatically add a trigger button
        showProgressDetails: true,
        proudlyDisplayPoweredByUppy: false, // Hide Uppy branding
        note: "PDF files only. Max 100MB.", // Inform user

        // theme: 'dark', // Optional: 'light' or 'dark' or 'auto'
      });
    };

    initializeUppy();

    // Cleanup function for when the component unmounts or dependencies change
    return () => {
      // Check if plugins exist before trying to remove them to prevent errors
      const dashboardPlugin = uppy.getPlugin('Dashboard');
      if (dashboardPlugin) {
        uppy.removePlugin(dashboardPlugin);
      }

      const tusPlugin = uppy.getPlugin('Tus');
      if (tusPlugin) {
        uppy.removePlugin(tusPlugin);
      }
      // uppy.close(); // Use close instead of reset if you might reuse the instance
    };
  }, [authorized, uppy]); // Dependencies: only run when auth status changes or uppy instance is created

  // --- TXT Uppy Initialization (Commented Out - Keep if needed) ---
  // useEffect(() => {
  //   if (!authorized || uppyTxt.getPlugin('Tus')) return;
  //   // ... similar initialization logic for uppyTxt targeting 'ragfiles' ...
  // }, [authorized, uppyTxt]);

  // --- Event Handlers ---
  const toggleFileSelection = (fileId: string) => {
    setSelectedFiles(prev =>
      prev.includes(fileId) ? prev.filter(id => id !== fileId) : [...prev, fileId]
    );
  };

  const toggleSelectAll = () => {
    if (selectedFiles.length === processedFiles.length) {
      setSelectedFiles([]);
    } else {
      setSelectedFiles(processedFiles.map(file => file.id));
    }
  };

  const handleDeleteFiles = async () => {
    if (selectedFiles.length === 0) return;

    const confirmed = window.confirm(
      `Are you sure you want to delete ${selectedFiles.length} file(s)? This will remove both .txt and .pdf versions. This cannot be undone.`
    );
    if (!confirmed) return;

    const supabase = createClient();
    setMessage("Deleting files...");

    // Get base filenames (no extensions) from selected .txt files
    const baseNames = files
      .filter(file => selectedFiles.includes(file.id))
      .map(file => file.name.replace(/\.txt$/, ''));

    // Build full filenames for deletion
    const txtFilesToDelete = baseNames.map(name => `${name}.txt`);
    const pdfFilesToDelete = baseNames.map(name => `${name}.pdf`);

    // Delete from ragfiles (txts)
    const { error: txtError } = await supabase.storage.from("ragfiles").remove(txtFilesToDelete);

    // Delete from pdf bucket
    const { error: pdfError } = await supabase.storage.from("pdf").remove(pdfFilesToDelete);

    // Handle errors
    if (txtError || pdfError) {
      console.error("Error deleting files:", { txtError, pdfError });
      setMessage(
        `Delete failed: ${txtError?.message || ''} ${pdfError?.message || ''}`.trim()
      );
      return;
    }

    // Update frontend state
    setFiles(prev =>
      prev.filter(file => !txtFilesToDelete.includes(file.name))
    );
    setSelectedFiles([]);
    setMessage(`${txtFilesToDelete.length} File(s) deleted ✅`);
  };

  const handleRefresh = async () => {
    if (!authorized) return;
    setSearchQuery('');
    setSelectedFiles([]);
    setMessage("Refreshing file list...");

    const supabase = createClient();
    const { data, error } = await supabase.storage.from("ragfiles").list(); // Re-fetch from 'ragfiles'
    if (error) {
      console.error("Error refreshing files:", error);
      setMessage(`Failed to refresh files: ${error.message}`);
      return;
    }
    const mapped = (data || [])
      .filter(f => f.name !== '.emptyFolderPlaceholder')
      .map((f): FileItem => ({
        id: f.id ?? f.name,
        name: f.name,
        size: f.metadata?.size ?? 0,
        lastModified: new Date(f.updated_at ?? f.created_at ?? Date.now()),
        type: f.metadata?.mimetype ?? 'text/plain'
      }));
    setFiles(mapped);
    setMessage(mapped.length > 0 ? "File list refreshed." : "No files found.");
  };


  // Rename functionality might require moving/renaming in Supabase storage - more complex
  const handleRename = (fileId: string, newName: string) => {
    console.warn("Rename functionality requires backend implementation (Supabase move/rename)");
    // Basic frontend update (doesn't persist)
    // setFiles(prev => prev.map(file => file.id === fileId ? { ...file, name: newName } : file));
    setMessage("Rename requires server-side implementation.");
  };

  const handleSort = (field: 'name' | 'size' | 'lastModified') => {
    setSortConfig(prev => ({
      field,
      direction: prev.field === field && prev.direction === 'asc' ? 'desc' : 'asc'
    }));
    setSortMenuOpen(false); // Close menu after selection
  };

  // Function to explicitly open the Uppy Dashboard modal
  const openUploadModal = () => {
    const dashboard = uppy.getPlugin('Dashboard') as InstanceType<typeof Dashboard> | undefined;
    if (dashboard) {
      dashboard.openModal();
    } else {
      console.error("Uppy Dashboard plugin not initialized.");
      setMessage("Upload module not ready. Please refresh.");
    }
  };

  // --- Derived State ---
  // Filter and sort files for display
  const processedFiles = [...files]
    .filter(file => file.name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      const { field, direction } = sortConfig;
      const multiplier = direction === 'asc' ? 1 : -1;

      if (field === 'name') {
        return multiplier * a.name.localeCompare(b.name);
      }
      if (field === 'size') {
        return multiplier * (a.size - b.size);
      }
      // Default to sorting by lastModified date
      return multiplier * (a.lastModified.getTime() - b.lastModified.getTime());
    });

  // --- Render Logic ---
  if (loading) return <div className="p-4 text-center text-gray-600">Checking access...</div>;
  if (authorized === false) return (
    <div className="p-6 text-center text-red-700 bg-red-50 rounded-lg shadow">
      <h1 className="text-xl font-semibold">Access Denied</h1>
      <p>You are not authorized to view this page.</p>
    </div>
  );
  // Render main file manager UI only if authorized
  return (
    // Use padding for overall spacing
    <div className="h-full flex flex-col p-4 md:p-6 bg-gray-50">

      {/* Header Section */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">File Storage</h1>
          <p className="text-gray-500 mt-1">Manage RAG text files and upload PDFs for processing.</p>
        </div>
        <div className="flex flex-wrap gap-2"> {/* Allow wrapping on small screens */}
          {/* Button to trigger Uppy modal */}
          <button
            onClick={openUploadModal}
            className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 transition duration-150 ease-in-out"
          >
            <UploadIcon className="w-4 h-4 mr-2" /> Upload PDF
          </button>
          {/* Delete Button */}
          <button
            onClick={handleDeleteFiles}
            disabled={selectedFiles.length === 0}
            className={`flex items-center px-4 py-2 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-offset-2 transition duration-150 ease-in-out ${selectedFiles.length > 0
              ? 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
          >
            <TrashIcon className="w-4 h-4 mr-2" /> Delete Selected
          </button>
        </div>
      </div>
      {isConverting && (
        <div className="mb-4 p-4 border border-blue-300 rounded bg-blue-50 text-blue-800 shadow-sm">
          <div className="font-semibold mb-2">Converting PDFs to text...</div>
          <div className="w-full bg-blue-100 h-2 rounded overflow-hidden">
            <div className="bg-blue-500 h-2 animate-pulse w-full" />
          </div>
        </div>
      )}
      {/* Wrap FileList in a container that allows scrolling if needed */}
      <div className="flex-grow overflow-auto border border-gray-200 rounded-lg bg-white shadow-sm">
        {/* Conditionally render FileList or a message if no files */}
        {processedFiles.length > 0 ? (
          <FileList
            files={processedFiles}
            selectedFiles={selectedFiles}
            onToggleSelect={toggleFileSelection}
            onToggleSelectAll={toggleSelectAll}
            onRename={handleRename} // Pass rename handler
          // sortConfig={sortConfig} // Pass sort config for header indicators
          // onSort={handleSort} // Allow clicking headers to sort
          />
        ) : (
          <div className="p-6 text-center text-gray-500">
            {searchQuery ? `No files found matching "${searchQuery}".` : "No files to display."}
          </div>
        )}
      </div>


      {/* Status Message Area */}
      {message && (
        <div className="mt-4 p-3 rounded-md text-sm bg-green-50 text-green-700 border border-green-200 shadow-sm">
          {message}
        </div>
      )}
    </div> // End main container
  );
}
