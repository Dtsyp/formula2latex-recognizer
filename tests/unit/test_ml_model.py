import base64
import pytest
from unittest.mock import Mock, patch
import io
from PIL import Image

with patch.dict('sys.modules', {
    'transformers': Mock(),
    'torch': Mock(),
    'torchvision': Mock()
}):
    import sys
    import os
    ml_path = os.path.join(os.path.dirname(__file__), '..', '..', 'ml')
    sys.path.insert(0, ml_path)
    
    from model import Formula2LaTeXModel


class TestFormula2LaTeXModel:
    
    @patch('model.TrOCRProcessor')
    @patch('model.VisionEncoderDecoderModel')
    @patch('model.torch')
    def test_model_initialization(self, mock_torch, mock_model_class, mock_processor_class):
        mock_torch.device.return_value = "cpu"
        
        model = Formula2LaTeXModel()
        
        assert model.model_name == "microsoft/trocr-base-printed"
        assert model.device == "cpu"

    def test_validate_image_valid_base64(self):
        image = Image.new('RGB', (100, 100), 'white')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        valid_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        model = Formula2LaTeXModel()
        result = model.validate_image(valid_base64)
        
        assert result['valid'] is True
        assert 'width' in result
        assert 'height' in result
        assert result['format'] == 'PNG'

    def test_validate_image_invalid_base64(self):
        invalid_base64 = "invalid_base64_string"
        
        model = Formula2LaTeXModel()
        result = model.validate_image(invalid_base64)
        
        assert result['valid'] is False
        assert 'error' in result

    def test_validate_image_not_image(self):
        text_base64 = base64.b64encode(b"not an image").decode('utf-8')
        
        model = Formula2LaTeXModel()
        result = model.validate_image(text_base64)
        
        assert result['valid'] is False
        assert 'error' in result

    @patch('model.Formula2LaTeXModel.load_model')
    def test_predict_success(self, mock_load_model):
        mock_processor = Mock()
        mock_model = Mock()
        mock_model.generate.return_value = [[1, 2, 3]]
        mock_processor.decode.return_value = "x^2 + y^2"
        
        model = Formula2LaTeXModel()
        model.processor = mock_processor
        model.model = mock_model
        
        image = Image.new('RGB', (100, 100), 'white')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        valid_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        result = model.predict(valid_base64)
        
        assert result['success'] is True
        assert result['latex_code'] == "x^2 + y^2"
        assert result['confidence'] > 0

    def test_predict_invalid_image(self):
        model = Formula2LaTeXModel()
        
        result = model.predict("invalid_base64")
        
        assert result['success'] is False
        assert result['error'] is not None
        assert result['latex_code'] is None

    @patch('model.Formula2LaTeXModel.load_model')
    def test_predict_model_error(self, mock_load_model):
        mock_processor = Mock()
        mock_model = Mock()
        mock_model.generate.side_effect = Exception("Model error")
        
        model = Formula2LaTeXModel()
        model.processor = mock_processor
        model.model = mock_model
        
        image = Image.new('RGB', (100, 100), 'white')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        valid_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        
        result = model.predict(valid_base64)
        
        assert result['success'] is False
        assert result['error'] is not None
        assert "Model error" in result['error']