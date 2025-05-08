export interface FileItem {
  id: string;
  name: string;
  type: string;
  size: number;
  lastModified: Date;
}
// Generate random file size between 10KB and 100MB
const randomSize = () => Math.floor(Math.random() * (100 * 1024 * 1024 - 10 * 1024) + 10 * 1024);
// Generate random date in the last 30 days
const randomDate = () => {
  const date = new Date();
  date.setDate(date.getDate() - Math.floor(Math.random() * 30));
  return date;
};
// Initial mock data
export const initialFiles: FileItem[] = [{
  id: "1",
  name: "annual-report-2023.pdf",
  type: "application/pdf",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "2",
  name: "product-image.jpg",
  type: "image/jpeg",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "3",
  name: "user-data.csv",
  type: "text/csv",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "4",
  name: "presentation.pptx",
  type: "application/vnd.openxmlformats-officedocument.presentationml.presentation",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "5",
  name: "project-plan.xlsx",
  type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "6",
  name: "company-logo.png",
  type: "image/png",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "7",
  name: "contract.docx",
  type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  size: randomSize(),
  lastModified: randomDate()
}, {
  id: "8",
  name: "video-tutorial.mp4",
  type: "video/mp4",
  size: randomSize(),
  lastModified: randomDate()
}];
// Helper function to format file size
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
}
// Helper function to get file icon based on type
export function getFileTypeIcon(type: string): string {
  if (type.includes("image")) return "image";
  if (type.includes("pdf")) return "pdf";
  if (type.includes("spreadsheet") || type.includes("csv") || type.includes("excel")) return "spreadsheet";
  if (type.includes("presentation")) return "presentation";
  if (type.includes("document") || type.includes("word")) return "document";
  if (type.includes("video")) return "video";
  if (type.includes("audio")) return "audio";
  return "file";
}