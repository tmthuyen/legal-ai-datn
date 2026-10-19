import { NextRequest, NextResponse } from 'next/server';

export const POST = async (req: NextRequest) => {
  return NextResponse.json(
    {
      status: 200,
      message: 'Login successful',
      data: {},
    },
    { status: 200 },
  );
};
