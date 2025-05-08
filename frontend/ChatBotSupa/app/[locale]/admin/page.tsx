"use client";

// import { useEffect, useState } from "react";
// import { useRouter } from "next/navigation"; // Import for navigation
// import { createClient } from "@/lib/supabase/client"; // Adjust path if needed
// import { redirect } from "next/navigation"
// import Uppy from "@uppy/core";
// import Tus from "@uppy/tus";
// import Dashboard from "@uppy/dashboard";
// import "@uppy/core/dist/style.min.css";
// import "@uppy/dashboard/dist/style.min.css";

// interface File {
//   name: string;
//   created_at: string;
//   id: string;
// }

// export default function AdminPage() {
//   const [loading, setLoading] = useState(true);
//   const [authorized, setAuthorized] = useState<boolean | null>(null);
//   const [message, setMessage] = useState("");
//   const [files, setFiles] = useState<File[]>([]);
//   const [uppy] = useState(() => new Uppy());
//   const router = useRouter(); // Initialize router

//   // Check admin role
//   useEffect(() => {
//     const checkRole = async () => {
//       const supabase = createClient();
//       const { data: { user } } = await supabase.auth.getUser();

//       if (!user) {
//         setAuthorized(false);
//         return;
//       }

//       const { data: profile, error } = await supabase
//         .from("profiles")
//         .select("role")
//         .eq("user_id", user.id)
//         .single();

//       if (error || !profile?.role || profile.role !== "admin") {
//         setAuthorized(false);
//         return;
//       }

//       setAuthorized(true);
//     };

//     checkRole().finally(() => setLoading(false));
//   }, []);

//   // Fetch list of files from the 'pdf' bucket
//   useEffect(() => {
//     if (!authorized) return;

//     const fetchFiles = async () => {
//       const supabase = createClient();
//       const { data, error } = await supabase.storage.from("pdf").list();

//       if (error) {
//         console.error("Error fetching files:", error);
//         setMessage(`Failed to load files: ${error.message}`);
//         return;
//       }

//       setFiles(data || []);
//     };

//     fetchFiles();
//   }, [authorized]);

//   // Initialize Uppy for modal upload
//   useEffect(() => {
//     if (!authorized) return;

//     const supabase = createClient();

//     const initializeUppy = async () => {
//       const { data: { session } } = await supabase.auth.getSession();

//       uppy.use(Tus, {
//         endpoint: `${process.env.NEXT_PUBLIC_SUPABASE_URL}/storage/v1/upload/resumable`,
//         retryDelays: [0, 3000, 5000, 10000, 20000],
//         headers: {
//           authorization: `Bearer ${session?.access_token}`,
//           apikey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "",
//         },
//         uploadDataDuringCreation: true,
//         removeFingerprintOnSuccess: true,
//         chunkSize: 6 * 1024 * 1024,
//         allowedMetaFields: [
//           "bucketName",
//           "objectName",
//           "contentType",
//           "cacheControl",
//         ],
//         onError: (error) => {
//           console.error("Upload error:", error);
//           setMessage(`Upload failed: ${error.message}`);
//         },
//       }).on("file-added", (file) => {
//         file.meta = {
//           ...file.meta,
//           bucketName: "pdf",
//           objectName: file.name,
//           contentType: file.type,
//           cacheControl: "3600",
//         };
//       }).on("upload-success", () => {
//         setMessage("Upload successful ✅");
//         // Refresh file list after successful upload
//         supabase.storage.from("pdf").list().then(({ data, error }) => {
//           if (!error) setFiles(data || []);
//         });
//       });

//       uppy.use(Dashboard, {
//         inline: false, // Modal instead of inline
//         target: "body",
//         showProgressDetails: true,
//         proudlyDisplayPoweredByUppy: false,
//         note: "PDF files only",
//         restrictions: {
//           allowedFileTypes: ["application/pdf"],
//         },
//       });
//     };

//     initializeUppy();

//     return () => {
//         uppy.cancelAll(); // ✅ stop uploads
//     };
//   }, [authorized, uppy]);

//   // Handle file deletion
//   const handleDelete = async (fileName: string) => {
//     if (!window.confirm(`Are you sure you want to delete ${fileName}?`)) return;

//     const supabase = createClient();
//     const { error } = await supabase.storage.from("pdf").remove([fileName]);

//     if (error) {
//       console.error("Error deleting file:", error);
//       setMessage(`Failed to delete ${fileName}: ${error.message}`);
//       return;
//     }

//     setMessage(`Deleted ${fileName} successfully 🗑️`);
//     // Refresh file list
//     const { data, error: listError } = await supabase.storage.from("pdf").list();
//     if (!listError) setFiles(data || []);
//   };

//   // Open Uppy Dashboard modal
//   const openUploadModal = () => {
//     uppy.getPlugin("Dashboard").openModal();
//   };

//   // Navigate to home route
//   const goToHome = () => {
//     router.push("/login");
//   };

//   if (loading) return <div className="p-4">Checking access...</div>;

//   if (authorized === false) {
//     return (
//       <div className="p-4 text-red-600">
//         <h1 className="text-xl font-semibold">You are not authorized to view this page.</h1>
//       </div>
//     );
//   }

//   return (
//     <div className="p-4 max-w-4xl mx-auto relative min-h-screen">
//       {/* Back Button */}
//       <button
//         onClick={goToHome}
//         className="absolute top-4 left-4 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
//       >
//         Back
//       </button>

//       <h1 className="text-2xl font-bold mb-4 mt-12">Admin Panel</h1>
//       <p className="mb-4">Welcome, admin. Below is the list of uploaded PDFs:</p>

//       {/* File List */}
//       {files.length > 0 ? (
//         <div className="mb-8">
//           <h2 className="text-lg font-semibold mb-2">Uploaded Files</h2>
//           <table className="w-full border-collapse">
//             <thead>
//               <tr className="bg-gray-100">
//                 <th className="border p-2 text-left">File Name</th>
//                 <th className="border p-2 text-left">Uploaded At</th>
//                 <th className="border p-2 text-left">Actions</th>
//               </tr>
//             </thead>
//             <tbody>
//               {files.map((file) => (
//                 <tr key={file.id}>
//                   <td className="border p-2">{file.name}</td>
//                   <td className="border p-2">
//                     {new Date(file.created_at).toLocaleString()}
//                   </td>
//                   <td className="border p-2">
//                     <button
//                       onClick={() => handleDelete(file.name)}
//                       className="bg-red-600 text-white px-3 py-1 rounded hover:bg-red-700 transition"
//                     >
//                       Delete
//                     </button>
//                   </td>
//                 </tr>
//               ))}
//             </tbody>
//           </table>
//         </div>
//       ) : (
//         <p className="mb-8 text-gray-600">No files uploaded yet.</p>
//       )}

//       {/* Message */}
//       {message && <p className="text-sm mb-4 text-green-600">{message}</p>}

//       {/* Upload Button */}
//       <button
//         onClick={openUploadModal}
//         className="fixed bottom-4 right-4 bg-blue-600 text-white px-6 py-3 rounded-full shadow-lg hover:bg-blue-700 transition"
//       >
//         Upload PDF
//       </button>
//     </div>
//   );
// }


// app/page.tsx
import React from 'react';
// import Layout from '@/components/Layout';
// import FileManager from '@/components/FileManager';
import Layout  from '../../../components/admin/Layout'
import FileManager from '../../../components/admin/FileManager'

export default function AdminPage() {
  return (
    <Layout>
      <FileManager />
    </Layout>
  );
}