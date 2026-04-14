package br.com.nathanfiorito.finances.infrastructure.telegram.file;

/**
 * Holds the result of downloading a file from Telegram.
 *
 * @param content   base64-encoded bytes for images, or raw text for PDFs with extractable text
 * @param entryType "image" or "pdf"
 */
public record DownloadedFile(String content, String entryType) {}
