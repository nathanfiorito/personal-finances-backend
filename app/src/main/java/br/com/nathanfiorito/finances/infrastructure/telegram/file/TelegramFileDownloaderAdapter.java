package br.com.nathanfiorito.finances.infrastructure.telegram.file;

import br.com.nathanfiorito.finances.domain.transaction.exceptions.LlmExtractionException;
import br.com.nathanfiorito.finances.infrastructure.telegram.config.TelegramProperties;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.extern.slf4j.Slf4j;
import org.apache.pdfbox.Loader;
import org.apache.pdfbox.pdmodel.PDDocument;
import org.apache.pdfbox.rendering.PDFRenderer;
import org.apache.pdfbox.text.PDFTextStripper;
import org.springframework.stereotype.Component;

import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Base64;

@Slf4j
@Component
public class TelegramFileDownloaderAdapter {

    private static final int MIN_TEXT_LENGTH = 50;
    private static final float RENDER_DPI = 150f;

    private final HttpClient http = HttpClient.newHttpClient();
    private final ObjectMapper objectMapper;
    private final String botApiBase;
    private final String fileApiBase;

    public TelegramFileDownloaderAdapter(TelegramProperties properties, ObjectMapper objectMapper) {
        this.objectMapper = objectMapper;
        String token = properties.getBotToken();
        this.botApiBase = "https://api.telegram.org/bot" + token;
        this.fileApiBase = "https://api.telegram.org/file/bot" + token;
    }

    /**
     * Downloads a file from Telegram and returns its content ready for the LLM.
     *
     * @param fileId   Telegram file_id
     * @param hintType "image" or "pdf"
     */
    public DownloadedFile download(String fileId, String hintType) {
        try {
            String filePath = getFilePath(fileId);
            byte[] bytes = downloadBytes(filePath);
            if ("pdf".equals(hintType)) {
                return processPdf(bytes);
            }
            return new DownloadedFile(Base64.getEncoder().encodeToString(bytes), "image");
        } catch (LlmExtractionException e) {
            throw e;
        } catch (Exception e) {
            throw new LlmExtractionException("Failed to download file from Telegram", e);
        }
    }

    // -------------------------------------------------------------------------
    // Private helpers
    // -------------------------------------------------------------------------

    private String getFilePath(String fileId) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(botApiBase + "/getFile?file_id=" + fileId))
            .GET()
            .build();
        HttpResponse<String> response = http.send(request, HttpResponse.BodyHandlers.ofString());
        JsonNode root = objectMapper.readTree(response.body());
        String filePath = root.path("result").path("file_path").asText(null);
        if (filePath == null || filePath.isBlank()) {
            throw new LlmExtractionException("Telegram getFile returned no file_path for fileId=" + fileId);
        }
        return filePath;
    }

    private byte[] downloadBytes(String filePath) throws Exception {
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(fileApiBase + "/" + filePath))
            .GET()
            .build();
        HttpResponse<byte[]> response = http.send(request, HttpResponse.BodyHandlers.ofByteArray());
        return response.body();
    }

    private DownloadedFile processPdf(byte[] bytes) {
        try (PDDocument doc = Loader.loadPDF(bytes)) {
            PDFTextStripper stripper = new PDFTextStripper();
            String text = stripper.getText(doc);
            if (text != null && text.strip().length() >= MIN_TEXT_LENGTH) {
                log.debug("PDF text extracted ({} chars)", text.strip().length());
                return new DownloadedFile(text, "pdf");
            }
            log.debug("PDF has no extractable text — rendering first page as image");
            return renderFirstPageAsImage(doc);
        } catch (IOException e) {
            throw new LlmExtractionException("Failed to process PDF", e);
        }
    }

    private DownloadedFile renderFirstPageAsImage(PDDocument doc) throws IOException {
        PDFRenderer renderer = new PDFRenderer(doc);
        BufferedImage image = renderer.renderImageWithDPI(0, RENDER_DPI);
        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        ImageIO.write(image, "JPEG", baos);
        return new DownloadedFile(Base64.getEncoder().encodeToString(baos.toByteArray()), "image");
    }
}
