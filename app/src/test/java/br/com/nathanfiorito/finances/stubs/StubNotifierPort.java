package br.com.nathanfiorito.finances.stubs;

import br.com.nathanfiorito.finances.domain.telegram.ports.NotifierPort;

import java.util.ArrayList;
import java.util.List;

public class StubNotifierPort implements NotifierPort {

    public record SentMessage(long chatId, String text, String parseMode, List<List<NotificationButton>> buttons) {}
    public record EditedMessage(long chatId, long messageId, String text, String parseMode, List<List<NotificationButton>> buttons) {}

    private final List<SentMessage> sentMessages = new ArrayList<>();
    private final List<EditedMessage> editedMessages = new ArrayList<>();
    private final List<String> answeredCallbacks = new ArrayList<>();

    @Override
    public void sendMessage(long chatId, String text, String parseMode, List<List<NotificationButton>> buttons) {
        sentMessages.add(new SentMessage(chatId, text, parseMode, buttons));
    }

    @Override
    public void editMessage(long chatId, long messageId, String text, String parseMode,
                            List<List<NotificationButton>> buttons) {
        editedMessages.add(new EditedMessage(chatId, messageId, text, parseMode, buttons));
    }

    @Override
    public void answerCallback(String callbackId, String text) {
        answeredCallbacks.add(callbackId);
    }

    @Override
    public void sendFile(long chatId, byte[] content, String filename, String caption) {}

    public List<SentMessage> sentMessages() { return sentMessages; }
    public List<EditedMessage> editedMessages() { return editedMessages; }
    public List<String> answeredCallbacks() { return answeredCallbacks; }

    public SentMessage lastSent() { return sentMessages.get(sentMessages.size() - 1); }
    public EditedMessage lastEdited() { return editedMessages.get(editedMessages.size() - 1); }
}
