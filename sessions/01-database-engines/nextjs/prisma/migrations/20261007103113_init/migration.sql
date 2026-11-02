-- CreateTable
CREATE TABLE "hello" (
    "id" SERIAL NOT NULL,
    "msg" TEXT NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "hello_pkey" PRIMARY KEY ("id")
);
