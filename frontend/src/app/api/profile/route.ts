import { NextRequest, NextResponse } from 'next/server';

export const GET = async (req: NextRequest) => {

  return NextResponse.json({}, { status: 200 });
};

export async function PUT(req: Request) {
  // const body = (await req.json()) as UpdateUserProfileInput;
  // const auth = await requireUser();
  // if (!auth.ok)
  //     return Response.json(
  //         { message: auth.message },
  //         { status: auth.status },
  //     );

  // const updated = await auth.di.profile.updateMyProfile.execute(
  //     auth.userId,
  //     body,
  // );
  // return Response.json(updated.toDTO());
}
