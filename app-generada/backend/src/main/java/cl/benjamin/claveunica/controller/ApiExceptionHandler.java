package cl.benjamin.claveunica.controller;

import org.springframework.http.*;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.*;
import java.util.*;

@RestControllerAdvice
public class ApiExceptionHandler {
  @ExceptionHandler(MethodArgumentNotValidException.class)
  @ResponseStatus(HttpStatus.BAD_REQUEST)
  public Map<String, Object> validation(MethodArgumentNotValidException ex) {
    return Map.of("error", "validation_error", "message", "Solicitud invalida", "fields", ex.getBindingResult().getFieldErrors().size());
  }

  @ExceptionHandler(Exception.class)
  @ResponseStatus(HttpStatus.INTERNAL_SERVER_ERROR)
  public Map<String, Object> generic(Exception ex) {
    return Map.of("error", "internal_error", "message", ex.getClass().getSimpleName());
  }
}
