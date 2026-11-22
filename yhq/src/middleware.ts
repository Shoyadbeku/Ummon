import { NextResponse, type NextRequest } from "next/server";

const GUEST_COOKIE = "yhq_gid";
const SESSION_COOKIE = "yhq_session";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // CSRF himoyasi: o'zgartiruvchi API so'rovlari faqat shu saytdan kelishi kerak
  if (pathname.startsWith("/api/") && !["GET", "HEAD", "OPTIONS"].includes(req.method)) {
    const origin = req.headers.get("origin");
    const host = req.headers.get("x-forwarded-host") ?? req.headers.get("host");
    if (origin) {
      try {
        if (new URL(origin).host !== host) {
          return NextResponse.json({ error: "Ruxsat etilmagan manba" }, { status: 403 });
        }
      } catch {
        return NextResponse.json({ error: "Ruxsat etilmagan manba" }, { status: 403 });
      }
    }
  }

  if (pathname.startsWith("/admin") && !req.cookies.get(SESSION_COOKIE)) {
    const url = req.nextUrl.clone();
    url.pathname = "/kirish";
    url.searchParams.set("next", pathname);
    return NextResponse.redirect(url);
  }

  const res = NextResponse.next();
  if (!req.cookies.get(GUEST_COOKIE)) {
    res.cookies.set(GUEST_COOKIE, crypto.randomUUID(), {
      httpOnly: true,
      sameSite: "lax",
      secure: process.env.NODE_ENV === "production" && !process.env.INSECURE_COOKIES,
      path: "/",
      maxAge: 60 * 60 * 24 * 365,
    });
  }
  return res;
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icons/|manifest.webmanifest|sw.js|uploads/).*)"],
};
