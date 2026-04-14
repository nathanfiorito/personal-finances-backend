package br.com.nathanfiorito.finances.domain.telegram.ports;

import java.util.List;

public interface NotifierPort {

    record NotificationButton(String text, String callbackData) {}

    void sendMessage(long chatId, String text, String parseMode, List<List<NotificationButton>> buttons);

    void editMessage(long chatId, long messageId, String text, String parseMode, List<List<NotificationButton>> buttons);

    void answerCallback(String callbackId, String text);

    void sendFile(long chatId, byte[] content, String filename, String caption);
}
