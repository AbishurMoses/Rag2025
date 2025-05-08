"use client"

import Link from "next/link"
import { FC } from "react"
import { SAULogoSVG } from "../icons/southern-logo-svg"

export const Brand: FC = () => {
  return (
    <Link
      className="flex cursor-pointer flex-col items-center hover:opacity-50"
      href="http"
      target="_blank"
      rel="noopener noreferrer"
    >
      <div className="mb-6">
        <SAULogoSVG scale={1} />
      </div>
      <div className="text-4xl font-bold tracking-wide">sauragflow</div>
    </Link>
  )
}
