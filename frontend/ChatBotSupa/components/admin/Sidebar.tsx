import React from 'react';
import { FolderIcon, UsersIcon, SettingsIcon, LayoutDashboardIcon, LogOutIcon } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { supabase } from "@/lib/supabase/browser-client"
export default function Sidebar() {
  const router = useRouter();
  const handleSignOut = async () => {
      await supabase.auth.signOut()
      router.push("/login")
      router.refresh()
      return
    }

  return <aside className="hidden md:flex flex-col w-64 bg-white border-r border-gray-200 h-full">
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-xl font-bold text-gray-800">Admin Console</h1>
      </div>
      <nav className="flex-1 p-4">
        <ul className="space-y-1">
          {/* <li>
            <a href="#" className="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100">
              <LayoutDashboardIcon className="w-5 h-5 mr-3" />
              Dashboard
            </a>
          </li> */}
          <li>
            <a href="#" className="flex items-center p-3 text-indigo-600 bg-indigo-50 rounded-lg font-medium">
              <FolderIcon className="w-5 h-5 mr-3" />
              File Storage
            </a>
          </li>
          {/* <li>
            <a href="#" className="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100">
              <UsersIcon className="w-5 h-5 mr-3" />
              Users
            </a>
          </li> */}
          {/* <li>
            <a href="#" className="flex items-center p-3 text-gray-700 rounded-lg hover:bg-gray-100">
              <SettingsIcon className="w-5 h-5 mr-3" />
              Settings
            </a>
          </li> */}
        </ul>
      </nav>
      <div className="p-4 border-t border-gray-200">
        <button className="flex items-center w-full p-3 text-gray-700 rounded-lg hover:bg-gray-100" 
        onClick={handleSignOut}>
          <LogOutIcon className="w-5 h-5 mr-3" />
          Logout
        </button>
      </div>
    </aside>;
}